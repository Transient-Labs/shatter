# Shatter

Shatter is the revolutionary smart contract mechanic developed by [Transient Labs](https://transientlabs.xyz).

## What is Shatter?
Up until now, a 1/1 NFT is just that: an ERC-721 NFT that represents a one-of-a-kind piece of art. 

Shatter introduces an entirely new dynamic between the artist and collector. Using the Shatter smart contract, the collector now has a choice: keep the piece as a true 1/1 ... or ... shatter the piece, converting the original artwork into editioned ERC-721 NFTs.

For more high level information, please visit [our website](https://transientlabs.xyz/shatter)

## How is this repo structured?
We use [eth-brownie](https://github.com/eth-brownie/brownie) for our development environment. All contracts are in the `contracts` folder and tests are in the `tests` folder.

### Contracts
The main shatter contract was developed as `Shatter.sol`. This contract is at the root level of the contracts folder and serves as a template for Transient Labs to build custom Shatter contracts.

Further within this folder, there are folders for implementing proxy patterns and a shatter registry.

#### ShatterCore and ShatterCreator
These two folders go hand-in-hand to implement a proxy-pattern.

The `ShatterCore` folder contains contracts representing the logic layer of the proxy-pattern. Each version will only be deployed once to appropriate blockchains. This document will be updated as the official versions are deployed.

The `ShatterCreator` folder contains contracts representing the proxy layer of the proxy-pattern. It uses ERC1967 for the proxy implementation slots. There are official and test versions. The test versions are only for local development testing and shall not be deployed to any running blockchain. You'll notice that the official creator contracts also register the proxy address in the Shatter Registry (more on this below).

##### Official ShatterCore Implementations
| Network | Address | Version |
| :-----: | :-----: | :-----: |
| Mainnet |  | 1 |
| Rinkeby | 0xdB733ea1Bf6a8DCD1318903E17e500EA38aA006d | 1 |

#### ShatterRegistry
Transient Labs has implemented an on-chain registry to authenticate official Shatter contracts. Simply implementing a shatter interface does not stop people from changing core logic and frauding collectors. This is why we have chosen this route.

The Shatter Registry also implements a proxy-pattern but one that is upgradeable. There is the registry interface and then the engine that actually provides the logic layer for the registry. The reason for making this upgradeable is that we anticipate more features to be needed, as the product develops.

##### Official ShatterRegistry Implementations
| Network | Address |
| :-----: | :-----: |
| Mainnet | 0xe02BE21210A6BaC9Db6509037071F1A65CA91C0f |
| Rinkeby | 0xFa72C510E819cA0C142Ce91973fC2f0739148dEC |

##### Official ShatterRegistryEngine Implementations
| Network | Address | Engine Version |
| :-----: | :-----: | :------------: |
| Mainnet | 0x31e91DA8Ec00A9E6d245b308386D18ba9B347f12 | V1 |
| Rinkeby | 0x83E501025C319ddac7bfC69741BEa5f410566b58 | V1 |

## Tests
The tests must be run separate as some tests alter the blockchain timestamp which can cause other test files to fail inadvertently. This can be worked on in the future but is not a great concern at the moment.

## License
This project is licensed under the Apache-2.0 license