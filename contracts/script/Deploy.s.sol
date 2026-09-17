// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import "forge-std/Script.sol";
import "../src/PlazaEscrow.sol";

contract DeployPlazaEscrow is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_KEY");
        address usdc = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913; // USDC on Base
        address oracle = 0x456Ef3C809bF1016A2a2A67946a4C6B13198755c; // Your Plaza server address
        address feeTo = 0xb838930bf3dFD467D30979E12c0a94286F86708D; // Your Plaza fee wallet
        
        vm.startBroadcast(deployerPrivateKey);
        PlazaEscrow esc = new PlazaEscrow(usdc, oracle, feeTo);
        console.log("PlazaEscrow deployed at:", address(esc));
        vm.stopBroadcast();
    }
}
