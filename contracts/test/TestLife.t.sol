// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import "forge-std/Test.sol";
import "../src/PlazaEscrow.sol";

contract MockUSDC {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    function mint(address to, uint256 a) external { balanceOf[to] += a; }
    
    function approve(address spender, uint256 a) external returns (bool) {
        allowance[msg.sender][spender] = a;
        return true;
    }
    
    function transfer(address to, uint256 a) external returns (bool) {
        balanceOf[msg.sender] -= a;
        balanceOf[to] += a;
        return true;
    }
    
    function transferFrom(address f, address t, uint256 a) external returns (bool) {
        require(allowance[f][msg.sender] >= a, "insufficient allowance");
        allowance[f][msg.sender] -= a;
        balanceOf[f] -= a;
        balanceOf[t] += a;
        return true;
    }
}

contract TestLife is Test {
    function testFullAutonomousLifecycle() public {
        MockUSDC usdc = new MockUSDC();
        address client = address(0xC1);
        address worker = address(0xB0);
        address oracle = address(0x0A);
        address feeTo  = address(0xFEE);
        
        usdc.mint(client, 1000e6); // Give client $1000
        
        PlazaEscrow esc = new PlazaEscrow(address(usdc), oracle, feeTo);
        
        // 1. Client approves and funds $100 job
        vm.prank(client);
        usdc.approve(address(esc), 100e6);
        
        vm.prank(client);
        uint256 id = esc.create(address(0), 100e6);
        assertEq(usdc.balanceOf(address(esc)), 100e6);
        
        // 2. Worker submits
        vm.prank(worker);
        esc.submit(id, keccak256("deliverable"));
        
        // 3. Oracle (AI Judge) releases -> worker 95, fee 5
        vm.prank(oracle);
        esc.oracleRelease(id);
        assertEq(usdc.balanceOf(worker), 95e6);
        assertEq(usdc.balanceOf(feeTo), 5e6);
        
        // 4. IMMORTALITY TEST: oracle dead, new job, worker self-claims after 4h
        vm.prank(client);
        usdc.approve(address(esc), 50e6);
        vm.prank(client);
        uint256 id2 = esc.create(address(0), 50e6);
        vm.prank(worker);
        esc.submit(id2, keccak256("work2"));
        vm.warp(block.timestamp + 4 hours + 1);
        vm.prank(worker);
        esc.claim(id2);
        assertEq(usdc.balanceOf(worker), 95e6 + 475e5);
        
        // 5. IMMORTALITY TEST: worker vanishes, client reclaims after 30d
        vm.prank(client);
        usdc.approve(address(esc), 60e6);
        vm.prank(client);
        uint256 id3 = esc.create(address(0), 60e6);
        vm.prank(worker);
        esc.submit(id3, keccak256("work3"));
        vm.warp(block.timestamp + 30 days + 1);
        vm.prank(client);
        esc.clientReclaim(id3);
        assertTrue(usdc.balanceOf(client) > 0);
        
        // 6. ATTACK TEST: self-dealing blocked
        vm.prank(client);
        usdc.approve(address(esc), 70e6);
        vm.prank(client);
        uint256 id4 = esc.create(address(0), 70e6);
        vm.prank(client);
        vm.expectRevert("no self-dealing");
        esc.submit(id4, keccak256("x"));
    }
}
