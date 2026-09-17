// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function transfer(address to, uint256 amt) external returns (bool);
    function transferFrom(address from, address to, uint256 amt) external returns (bool);
}

/// @title PlazaEscrow - immortal agent-to-agent escrow
/// @notice Funds live in the contract. Oracle (Plaza server) signs releases but holds NO funds.
///         If oracle dies, workers self-claim after the window. If worker vanishes, client reclaims after 30d.
contract PlazaEscrow {
    IERC20 public usdc;
    address public oracle;
    address public feeTo;
    uint256 public feeBps = 500;              // 5%
    uint256 public claimDelay = 4 hours;      // worker self-claim window
    uint256 public reclaimDelay = 30 days;    // client safety net
    uint256 public minEscrow = 50e6;          // $50 (6 decimals)
    uint256 public nextId = 1;

    struct Job {
        address client;
        address worker;
        uint256 amount;
        uint8 status;          // 0 funded, 1 submitted, 2 released, 3 refunded
        uint64 submittedAt;
        bytes32 deliverableHash;
    }
    mapping(uint256 => Job) public jobs;

    event Created(uint256 indexed id, address client, uint256 amount);
    event Submitted(uint256 indexed id, address worker, bytes32 hash);
    event Released(uint256 indexed id, address worker, uint256 payout, uint256 fee);
    event Refunded(uint256 indexed id, address client, uint256 amount);

    constructor(address _usdc, address _oracle, address _feeTo) {
        usdc = IERC20(_usdc);
        oracle = _oracle;
        feeTo = _feeTo;
    }

    function create(address worker, uint256 amount) external returns (uint256 id) {
        require(amount >= minEscrow, "min $50");
        require(usdc.transferFrom(msg.sender, address(this), amount), "fund failed");
        id = nextId++;
        jobs[id] = Job(msg.sender, worker, amount, 0, 0, bytes32(0));
        emit Created(id, msg.sender, amount);
    }

    function submit(uint256 id, bytes32 hash) external {
        Job storage j = jobs[id];
        require(j.status == 0, "not open");
        require(j.worker == address(0) || j.worker == msg.sender, "assigned elsewhere");
        require(j.client != msg.sender, "no self-dealing");
        j.worker = msg.sender;
        j.status = 1;
        j.submittedAt = uint64(block.timestamp);
        j.deliverableHash = hash;
        emit Submitted(id, msg.sender, hash);
    }

    function oracleRelease(uint256 id) external {
        require(msg.sender == oracle, "only oracle");
        _release(id);
    }

    function oracleRefund(uint256 id) external {
        require(msg.sender == oracle, "only oracle");
        _refund(id);
    }

    /// Happy path: client approves early release -> worker paid instantly
    function clientRelease(uint256 id) external {
        Job storage j = jobs[id];
        require(j.status == 1, "not submitted");
        require(j.client == msg.sender, "only client");
        _release(id);
    }

    /// IMMORTALITY: oracle dead? worker self-claims after the window.
    function claim(uint256 id) external {
        Job storage j = jobs[id];
        require(j.status == 1, "not submitted");
        require(j.worker == msg.sender, "only worker");
        require(block.timestamp >= j.submittedAt + claimDelay, "window open");
        _release(id);
    }

    /// IMMORTALITY: worker vanished? client reclaims after 30 days.
    function clientReclaim(uint256 id) external {
        Job storage j = jobs[id];
        require(j.status == 1, "not submitted");
        require(j.client == msg.sender, "only client");
        require(block.timestamp >= j.submittedAt + reclaimDelay, "too early");
        _refund(id);
    }

    function _release(uint256 id) internal {
        Job storage j = jobs[id];
        require(j.status == 1, "bad state");
        j.status = 2;
        uint256 fee = (j.amount * feeBps) / 10000;
        usdc.transfer(j.worker, j.amount - fee);
        usdc.transfer(feeTo, fee);
        emit Released(id, j.worker, j.amount - fee, fee);
    }

    function _refund(uint256 id) internal {
        Job storage j = jobs[id];
        require(j.status == 1, "bad state");
        j.status = 3;
        usdc.transfer(j.client, j.amount);
        emit Refunded(id, j.client, j.amount);
    }
}
