# Shatter

Shatter is the revolutionary smart contract mechanic developed by [Transient Labs](https://transientlabs.xyz).

## What is Shatter?
Up until now, a 1/1 NFT is just that: an ERC-721 NFT that represents a one-of-a-kind piece of art. 

Shatter introduces an entirely new dynamic between the artist and collector. Using the Shatter smart contract, the collector now has a choice: keep the piece as a true 1/1 ... or ... shatter the piece, converting the original artwork into editioned ERC-721 NFTs.

For more high level information, please visit [our website](https://transientlabs.xyz/shatter)

## How is this repo structured?
We use [eth-brownie](https://github.com/eth-brownie/brownie) for our development environment. All contracts are in the `contracts` folder and tests are in the `tests` folder.

### Contracts
The base ERC721 contract is `ERC721S.sol`. This was forked from OpenZeppelin. This was done to implement an efficient batch mint while keeping all transfer costs low. ERC721A was initially used but any Shatters above 150 have expensive transfer costs associated. The Shatter implementation was able to reduce costs by about 50% for this speicific implementation (more details below). The two changes implemented in `ERC721S.sol` are as follows:
1. `_owners` and `_balances` variable scope were changed to `internal`
2. All calls to `ERC721.ownerOf` were changed to `ownerOf` as this function is reimplemented in each Shatter contract for efficient batch minting

The main implementations of Shatter contracts are in the main `contracts` folder. Each Shatter is called `ShatterV<version>.sol`, such as `ShatterV1.sol` and `ShatterV2.sol`.

#### Gas Comparison Using ERC721S.sol versus ERC721A.sol
The following values are worst case values found during testing. Both Shatter test with 100 tokens and fuse back to 1 token. Both tests for safeTransferFrom transfer token id 100.
| Function | ShatterV1.sol with ERC721S.sol | ShatterV1.sol with ERC721A.sol | Savings with ERC721S.sol |
| :------: | :------: | :-----: | :-----: |
| mint | 333079 | 351239 | 5.17% |
| shatter | 278763 | 320002 | 12.89% |
| fuse | 1740811 | 3491396 | 50.14% |
| safeTransferFrom | 83809 | 167281 | 49.90% |

Further within this folder, there are folders for implementing proxy patterns and a shatter registry.

#### ShatterCore and ShatterCreator
These two folders go hand-in-hand to implement a proxy-pattern.

The `ShatterCore` folder contains contracts representing the logic layer of the proxy-pattern. Each version will only be deployed once to appropriate blockchains. This document will be updated as the official versions are deployed.

The `ShatterCreator` folder contains contracts representing the proxy layer of the proxy-pattern. It uses ERC1967 for the proxy implementation slots. There are official and test versions. The test versions are only for local development testing and shall not be deployed to any running blockchain. You'll notice that the official creator contracts also register the proxy address in the Shatter Registry (more on this below).

##### Official ShatterCore Implementations
| Network | Address | Version |
| :-----: | :-----: | :-----: |
| Mainnet |  | 1 |
| Rinkeby |  | 1 |
| Mainnet |  | 2 |
| Rinkeby |  | 2 |

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