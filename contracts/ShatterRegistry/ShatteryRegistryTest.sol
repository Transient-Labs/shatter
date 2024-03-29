// SPDX-License-Identifier: Apache-2.0

/// @title Shatter Registry
/// @author transientlabs.xyz

pragma solidity ^0.8.9;

import "OpenZeppelin/openzeppelin-contracts@4.6.0/contracts/proxy/ERC1967/ERC1967Proxy.sol";

contract ShatterRegistryTest is ERC1967Proxy {
    constructor(address _impAddr) ERC1967Proxy(_impAddr, abi.encodeWithSignature("initialize()")) {}
}