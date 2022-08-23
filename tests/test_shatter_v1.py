from brownie import ShatterV1, accounts, reverts, chain
import pytest
import base64
import json
from random import randint

shatter_time = int(chain.time() + 2 * 3600)

@pytest.fixture(scope="class")
def contract():
    return ShatterV1.deploy("Test", "TST", accounts[1].address, 500, accounts[2].address, 1, 100, shatter_time, {"from": accounts[0]})

class TestDefault:

    def test_default_values(self, contract):
        recp, amt = contract.royaltyInfo(1, 10000)
        assert (
            contract.name() == "Test" and
            contract.symbol() == "TST" and
            contract.minShatters() == 1 and
            contract.maxShatters() == 100 and
            contract.shatterTime() == shatter_time and
            recp == accounts[1].address and
            amt == 500
        )

class TestInterface:

    def test_erc721_interface(self, contract):
        assert contract.supportsInterface("0x80ac58cd")

    def test_eip2981_interface(self, contract):
        assert contract.supportsInterface("0x2a55205a")

    def test_erc165_interface(self, contract):
        assert contract.supportsInterface("0x01ffc9a7")

    def test_erc721_metadata_interface(self, contract):
        assert contract.supportsInterface("0x5b5e139f")

class TestERC721Init:
    def test_balance_of_zero_address(self, contract):
        with reverts("ERC721: address zero is not a valid owner"):
            contract.balanceOf(f"0x{bytes(20).hex()}")

    def test_balance_of_no_tokens_minted(self, contract):
        assert contract.balanceOf(accounts[0].address) == 0

    def test_owner_of_invalid_token(self, contract):
        with reverts("ERC721: invalid token ID"):
            contract.ownerOf(0)

    def test_name(self, contract):
        assert contract.name() == "Test"

    def test_symbol(self, contract):
        assert contract.symbol() == "TST"

    def test_token_uri_no_tokens(self, contract):
        with reverts("ERC721: invalid token ID"):
            contract.tokenURI(0)

    def test_approve_no_tokens(self, contract):
        with reverts("ERC721: invalid token ID"):
            contract.approve(accounts[1].address, 0, {"from": accounts[0]})

    def test_get_approved_no_tokens(self, contract):
        with reverts("ERC721: invalid token ID"):
            contract.getApproved(0)

    def test_set_approval_for_all_operator_is_owner(self, contract):
        with reverts("ERC721: approve to caller"):
            contract.setApprovalForAll(accounts[0].address, True, {"from": accounts[0]})

    def test_set_approval_for_all_true(self, contract):
        tx = contract.setApprovalForAll(accounts[1].address, True, {"from": accounts[0]})
        assert(
            contract.isApprovedForAll(accounts[0].address, accounts[1].address) is True and
            tx.events["ApprovalForAll"]["approved"] is True and
            tx.events["ApprovalForAll"]["owner"] == accounts[0].address and
            tx.events["ApprovalForAll"]["operator"] == accounts[1].address
        )

    def test_set_approval_for_all_false(self, contract):
        tx = contract.setApprovalForAll(accounts[1].address, False, {"from": accounts[0]})
        assert(
            contract.isApprovedForAll(accounts[0].address, accounts[1].address) is False and
            tx.events["ApprovalForAll"]["approved"] is False and
            tx.events["ApprovalForAll"]["owner"] == accounts[0].address and
            tx.events["ApprovalForAll"]["operator"] == accounts[1].address
        )

    
class TestNoUserAccess:

    def test_set_royalty_info(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.setRoyaltyInfo(accounts[3].address, 750, {"from": accounts[3]})

    def test_renounce_admin(self, contract):
        with reverts("Address not admin"):
            contract.renounceAdmin({"from": accounts[3]})

    def test_set_admin_address(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.setAdminAddress(accounts[1].address, {"from": accounts[3]})

    def test_mint(self, contract):
        with reverts("Address not admin or owner"):
            contract.mint("test/", {"from": accounts[3]})

class TestAdminAccess:

    def test_set_royalty_info(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.setRoyaltyInfo(accounts[3].address, 750, {"from": accounts[2]})

    def test_set_admin_address(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.setAdminAddress(accounts[1].address, {"from": accounts[2]})
  
    def test_mint(self, contract):
        contract.mint("test/", {"from": accounts[2]})
        assert contract.ownerOf(0) == accounts[0].address

    def test_shatter(self, contract):
        with reverts("Caller is not owner of token 0"):
            contract.shatter(10, {"from": accounts[2]})

    def test_fuse(self, contract):
        with reverts("Can't fuse if not already shattered"):
            contract.fuse({"from": accounts[2]})

    def test_renounce_admin(self, contract):
        contract.renounceAdmin({"from": accounts[2]})
        assert contract.adminAddress() == f"0x{bytes(20).hex()}"

class TestOwnerAccess:

    def test_set_royalty_info(self, contract):
        contract.setRoyaltyInfo(accounts[3].address, 750, {"from": accounts[0]})
        (recp, amt) = contract.royaltyInfo(1, 1000)
        assert recp == accounts[3].address and amt == 1000*0.075

    def test_renounce_admin(self, contract):
        with reverts("Address not admin"):
            contract.renounceAdmin({"from": accounts[0]})

    def test_set_admin(self, contract):
        contract.setAdminAddress(accounts[1].address, {"from": accounts[0]})
        assert contract.adminAddress() == accounts[1].address
    
    def test_mint(self, contract):
        contract.mint("test/", {"from": accounts[0]})
        assert contract.ownerOf(0) == accounts[0].address

class TestERC721AfterMint:
    def test_mint(self, contract):
        contract.mint("test/", {"from": accounts[0]})
        assert contract.ownerOf(0) == accounts[0].address and contract.balanceOf(accounts[0].address) == 1

    def test_mint_again(self, contract):
        with reverts("Already minted the first piece"):
            contract.mint("test/", {"from": accounts[0]})

    def test_approve_token_0(self, contract):
        tx = contract.approve(accounts[5].address, 0, {"from": accounts[0]})
        assert(
            contract.getApproved(0) == accounts[5].address and
            tx.events["Approval"]["owner"] == accounts[0].address and
            tx.events["Approval"]["approved"] == accounts[5].address and
            tx.events["Approval"]["tokenId"] == 0
        )
    
    def test_approve_nonexistent_token(self, contract):
        with reverts("ERC721: invalid token ID"):
            contract.approve(accounts[5].address, 1, {"from": accounts[0]})

    def test_approve_non_owner_of_token(self, contract):
        with reverts("ERC721: approve caller is not token owner or approved for all"):
            contract.approve(accounts[5].address, 0, {"from": accounts[5]})

    def test_approval_for_all(self, contract):
        contract.setApprovalForAll(accounts[6].address, True, {"from": accounts[0]})
        assert contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True

    def test_approve_if_approved_for_all(self, contract):
        contract.approve(accounts[4].address, 0, {"from": accounts[6]})

    def test_transfer_not_owner_or_approved(self, contract):
        with reverts("ERC721: caller is not token owner or approved"):
            contract.transferFrom(accounts[0].address, accounts[7].address, 0, {"from": accounts[7]})

    def test_transfer_approved(self, contract):
        contract.transferFrom(accounts[0].address, accounts[1].address, 0, {"from": accounts[4]})
        assert(
            contract.ownerOf(0) == accounts[1].address and
            contract.balanceOf(accounts[1].address) == 1 and
            contract.getApproved(0) == f"0x{bytes(20).hex()}"
        )

    def test_transfer_from_owner(self, contract):
        contract.transferFrom(accounts[1].address, accounts[0].address, 0, {"from": accounts[1]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1 and
            contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True
        )

    def test_transfer_from_approved_for_all(self, contract):
        contract.transferFrom(accounts[0].address, accounts[8].address, 0, {"from": accounts[6]})
        assert(
            contract.ownerOf(0) == accounts[8].address and
            contract.balanceOf(accounts[8].address) == 1
        )

    def test_transfer_owner_again(self, contract):
        contract.transferFrom(accounts[8].address, accounts[0].address, 0, {"from": accounts[8]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1
        )

    def test_safe_transfer_not_owner_or_approved(self, contract):
        with reverts("ERC721: caller is not token owner or approved"):
            contract.safeTransferFrom(accounts[0].address, accounts[7].address, 0, {"from": accounts[7]})

    def test_safe_transfer_bad_contract(self, contract):
        with reverts("ERC721: transfer to non ERC721Receiver implementer"):
            contract.safeTransferFrom(accounts[0].address, contract.address, 0, {"from": accounts[0]})

    def test_safe_transfer_approved(self, contract):
        contract.approve(accounts[4].address, 0, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[1].address, 0, {"from": accounts[4]})
        assert(
            contract.ownerOf(0) == accounts[1].address and
            contract.balanceOf(accounts[1].address) == 1 and
            contract.getApproved(0) == f"0x{bytes(20).hex()}"
        )

    def test_safe_transfer_from_owner(self, contract):
        contract.safeTransferFrom(accounts[1].address, accounts[0].address, 0, {"from": accounts[1]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1 and
            contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True
        )

    def test_safe_transfer_from_approved_for_all(self, contract):
        contract.safeTransferFrom(accounts[0].address, accounts[8].address, 0, {"from": accounts[6]})
        assert(
            contract.ownerOf(0) == accounts[8].address and
            contract.balanceOf(accounts[8].address) == 1
        )

class TestShatter:

    def test_shatter_non_owner(self, contract):
        contract.mint("test/", {"from": accounts[0]})
        with reverts("Caller is not owner of token 0"):
            contract.shatter(10, {"from": accounts[1]})

    def test_shatter_less_than_min(self, contract):
        with reverts("Cannot set number of editions above max or below the min"):
            contract.shatter(0, {"from": accounts[0]})

    def test_shatter_more_than_max(self, contract):
        with reverts("Cannot set number of editions above max or below the min"):
            contract.shatter(101, {"from": accounts[0]})

    def test_shatter_before_shatter_time(self, contract):
        with reverts("Cannot shatter prior to shatterTime"):
            contract.shatter(10, {"from": accounts[0]})

    def test_create_max_shatter(self, contract):
        t = int(shatter_time - chain.time())
        chain.sleep(t)
        contract.shatter(100, {"from": accounts[0]})
        assert contract.balanceOf(accounts[0].address) == 100

    def test_owner_of(self, contract):
        assert contract.ownerOf(1) == accounts[0].address

    def test_worst_case_transfer_cost(self, contract):
        contract.safeTransferFrom(accounts[0].address, accounts[1].address, 100, {"from": accounts[0]})

    def test_shatter_again(self, contract):
        with reverts("Already is shattered"):
            contract.shatter(100, {"from": accounts[0]})

class TestShatterByFirstBuyer:

    def test_shatter(self, contract):
        contract.mint("test/", {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[5].address, 0, {"from": accounts[0]})
        contract.shatter(10, {"from": accounts[5]})
        assert contract.balanceOf(accounts[5].address) == 10

class TestShatterMultipleTransfers:

    def test_shatter(self, contract):
        contract.mint("test/", {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[5].address, 0, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[5].address, accounts[6].address, 0, {"from": accounts[5]})
        contract.shatter(10, {"from": accounts[6]})
        assert contract.balanceOf(accounts[6].address) == 10

class TestERC721MultiShatter:
    def test_mint_and_shatter(self, contract):
        tx1 = contract.mint("test/", {"from": accounts[0]})
        tx2 = contract.shatter(100, {"from": accounts[0]})
        owner_tf = True
        for i in range(1, 101):
            owner_tf = owner_tf and contract.ownerOf(i) == accounts[0].address
        assert(
            owner_tf == True and
            len(tx1.events) == 1 and
            len(tx2.events) == 102 and # 100 transfer from 0 address + 1 transfer to 0 address + Shatter event
            contract.balanceOf(accounts[0].address) == 100
        )

    def test_approve_nonexistent_token(self, contract):
        with reverts("Invalid token id"):
            contract.approve(accounts[5].address, 101, {"from": accounts[0]})

    def test_approve_and_transfer_for_3_random_tokens(self, contract):
        for i in range(3):
            id = randint(2, 50)
            contract.approve(accounts[4+i].address, id, {"from": accounts[0]})
            contract.transferFrom(accounts[0].address, accounts[5+i].address, id, {"from": accounts[4+i]})
            assert contract.ownerOf(id) == accounts[5+i].address
        assert contract.balanceOf(accounts[0].address) == 97

    def test_approve_for_all_and_transfer(self, contract):
        contract.setApprovalForAll(accounts[8].address, True, {"from": accounts[0]})
        contract.transferFrom(accounts[0].address, accounts[9].address, 1, {"from": accounts[8]})
        assert contract.balanceOf(accounts[0].address) == 96 and contract.ownerOf(1) == accounts[9].address

    def test_approve_and_safe_transfer_for_3_random_tokens(self, contract):
        for i in range(3):
            id = randint(51, 99)
            contract.approve(accounts[4+i].address, id, {"from": accounts[0]})
            contract.safeTransferFrom(accounts[0].address, accounts[5+i].address, id, {"from": accounts[4+i]})
            assert contract.ownerOf(id) == accounts[5+i].address
        assert contract.balanceOf(accounts[0].address) == 93

    def test_approve_for_all_and_safe_transfer(self, contract):
        contract.setApprovalForAll(accounts[8].address, True, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[9].address, 100, {"from": accounts[8]})
        assert contract.balanceOf(accounts[0].address) == 92 and contract.ownerOf(100) == accounts[9].address

class TestERC721SingleShatter:
    def test_mint_and_shatter(self, contract):
        tx1 = contract.mint("test/", {"from": accounts[0]})
        tx2 = contract.shatter(1, {"from": accounts[0]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            len(tx1.events) == 1 and
            len(tx2.events) == 2 and # Shatter event + Fuse event
            contract.balanceOf(accounts[0].address) == 1
        )

    def test_mint_again(self, contract):
        with reverts("Already minted the first piece"):
            contract.mint("test/", {"from": accounts[0]})

    def test_approve_token_0(self, contract):
        tx = contract.approve(accounts[5].address, 0, {"from": accounts[0]})
        assert(
            contract.getApproved(0) == accounts[5].address and
            tx.events["Approval"]["owner"] == accounts[0].address and
            tx.events["Approval"]["approved"] == accounts[5].address and
            tx.events["Approval"]["tokenId"] == 0
        )
    
    def test_approve_nonexistent_token(self, contract):
        with reverts("ERC721: invalid token ID"):
            contract.approve(accounts[5].address, 1, {"from": accounts[0]})

    def test_approve_non_owner_of_token(self, contract):
        with reverts("ERC721: approve caller is not token owner or approved for all"):
            contract.approve(accounts[5].address, 0, {"from": accounts[5]})

    def test_approval_for_all(self, contract):
        contract.setApprovalForAll(accounts[6].address, True, {"from": accounts[0]})
        assert contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True

    def test_approve_if_approved_for_all(self, contract):
        contract.approve(accounts[4].address, 0, {"from": accounts[6]})

    def test_transfer_not_owner_or_approved(self, contract):
        with reverts("ERC721: caller is not token owner or approved"):
            contract.transferFrom(accounts[0].address, accounts[7].address, 0, {"from": accounts[7]})

    def test_transfer_approved(self, contract):
        contract.transferFrom(accounts[0].address, accounts[1].address, 0, {"from": accounts[4]})
        assert(
            contract.ownerOf(0) == accounts[1].address and
            contract.balanceOf(accounts[1].address) == 1 and
            contract.getApproved(0) == f"0x{bytes(20).hex()}"
        )

    def test_transfer_from_owner(self, contract):
        contract.transferFrom(accounts[1].address, accounts[0].address, 0, {"from": accounts[1]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1 and
            contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True
        )

    def test_transfer_from_approved_for_all(self, contract):
        contract.transferFrom(accounts[0].address, accounts[8].address, 0, {"from": accounts[6]})
        assert(
            contract.ownerOf(0) == accounts[8].address and
            contract.balanceOf(accounts[8].address) == 1
        )

    def test_transfer_owner_again(self, contract):
        contract.transferFrom(accounts[8].address, accounts[0].address, 0, {"from": accounts[8]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1
        )

    def test_safe_transfer_not_owner_or_approved(self, contract):
        with reverts("ERC721: caller is not token owner or approved"):
            contract.safeTransferFrom(accounts[0].address, accounts[7].address, 0, {"from": accounts[7]})

    def test_safe_transfer_bad_contract(self, contract):
        with reverts("ERC721: transfer to non ERC721Receiver implementer"):
            contract.safeTransferFrom(accounts[0].address, contract.address, 0, {"from": accounts[0]})

    def test_safe_transfer_approved(self, contract):
        contract.approve(accounts[4].address, 0, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[1].address, 0, {"from": accounts[4]})
        assert(
            contract.ownerOf(0) == accounts[1].address and
            contract.balanceOf(accounts[1].address) == 1 and
            contract.getApproved(0) == f"0x{bytes(20).hex()}"
        )

    def test_safe_transfer_from_owner(self, contract):
        contract.safeTransferFrom(accounts[1].address, accounts[0].address, 0, {"from": accounts[1]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1 and
            contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True
        )

    def test_safe_transfer_from_approved_for_all(self, contract):
        contract.safeTransferFrom(accounts[0].address, accounts[8].address, 0, {"from": accounts[6]})
        assert(
            contract.ownerOf(0) == accounts[8].address and
            contract.balanceOf(accounts[8].address) == 1
        )

class TestFuse:
    def test_fuse_not_shattered(self, contract):
        contract.mint("test/", {"from": accounts[0]})
        with reverts("Can't fuse if not already shattered"):
            contract.fuse({"from": accounts[0]})

    def test_fuse_not_owner_of_all(self, contract):
        contract.shatter(100, {'from': accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[1].address, 1, {"from": accounts[0]})
        with reverts():
            contract.fuse({"from": accounts[0]})

    def test_fuse_not_own_any(self, contract):
        with reverts():
            contract.fuse({"from": accounts[6]})

    def test_fuse_own_one(self, contract):
        with reverts():
            contract.fuse({"from": accounts[1]})

    def test_fuse(self, contract):
        contract.safeTransferFrom(accounts[1].address, accounts[0].address, 1, {"from": accounts[1]})
        contract.fuse({"from": accounts[0]})
        assert contract.balanceOf(accounts[0].address) == 1 and contract.ownerOf(0) == accounts[0].address

    def test_fuse_again(self, contract):
        with reverts("Already is fused"):
            contract.fuse({"from": accounts[0]})

class TestERC721BuyerFuse:
    def test_mint_shatter_fuse(self, contract):
        tx1 = contract.mint("test/", {"from": accounts[0]})
        tx2 = contract.shatter(75, {"from": accounts[0]})
        owner_tf = True
        for i in range(1, 76):
            contract.safeTransferFrom(accounts[0].address, accounts[5].address, i, {"from": accounts[0]})
            owner_tf = owner_tf and contract.ownerOf(i) == accounts[5].address
        tx3 = contract.fuse({"from": accounts[5]})
        assert(
            owner_tf and
            contract.ownerOf(0) == accounts[5].address and
            len(tx1.events) == 1 and
            len(tx2.events) == 77 and # 75 mints, 1 burn, 1 Shatter
            len(tx3.events) == 77 and # 75 burns, 1 mint, 1 Fuse
            contract.balanceOf(accounts[5].address) == 1
        )

    def test_safe_transfer_from(self, contract):
        contract.safeTransferFrom(accounts[5].address, accounts[0].address, 0, {"from": accounts[5]})
        assert contract.ownerOf(0) == accounts[0].address and contract.balanceOf(accounts[0].address) == 1

    def test_mint_again(self, contract):
        with reverts("Already minted the first piece"):
            contract.mint("test/", {"from": accounts[0]})

    def test_approve_token_0(self, contract):
        tx = contract.approve(accounts[5].address, 0, {"from": accounts[0]})
        assert(
            contract.getApproved(0) == accounts[5].address and
            tx.events["Approval"]["owner"] == accounts[0].address and
            tx.events["Approval"]["approved"] == accounts[5].address and
            tx.events["Approval"]["tokenId"] == 0
        )
    
    def test_approve_nonexistent_token(self, contract):
        with reverts("ERC721: invalid token ID"):
            contract.approve(accounts[5].address, 1, {"from": accounts[0]})

    def test_approve_non_owner_of_token(self, contract):
        with reverts("ERC721: approve caller is not token owner or approved for all"):
            contract.approve(accounts[5].address, 0, {"from": accounts[5]})

    def test_approval_for_all(self, contract):
        contract.setApprovalForAll(accounts[6].address, True, {"from": accounts[0]})
        assert contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True

    def test_approve_if_approved_for_all(self, contract):
        contract.approve(accounts[4].address, 0, {"from": accounts[6]})

    def test_transfer_not_owner_or_approved(self, contract):
        with reverts("ERC721: caller is not token owner or approved"):
            contract.transferFrom(accounts[0].address, accounts[7].address, 0, {"from": accounts[7]})

    def test_transfer_approved(self, contract):
        contract.transferFrom(accounts[0].address, accounts[1].address, 0, {"from": accounts[4]})
        assert(
            contract.ownerOf(0) == accounts[1].address and
            contract.balanceOf(accounts[1].address) == 1 and
            contract.getApproved(0) == f"0x{bytes(20).hex()}"
        )

    def test_transfer_from_owner(self, contract):
        contract.transferFrom(accounts[1].address, accounts[0].address, 0, {"from": accounts[1]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1 and
            contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True
        )

    def test_transfer_from_approved_for_all(self, contract):
        contract.transferFrom(accounts[0].address, accounts[8].address, 0, {"from": accounts[6]})
        assert(
            contract.ownerOf(0) == accounts[8].address and
            contract.balanceOf(accounts[8].address) == 1
        )

    def test_transfer_owner_again(self, contract):
        contract.transferFrom(accounts[8].address, accounts[0].address, 0, {"from": accounts[8]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1
        )

    def test_safe_transfer_not_owner_or_approved(self, contract):
        with reverts("ERC721: caller is not token owner or approved"):
            contract.safeTransferFrom(accounts[0].address, accounts[7].address, 0, {"from": accounts[7]})

    def test_safe_transfer_bad_contract(self, contract):
        with reverts("ERC721: transfer to non ERC721Receiver implementer"):
            contract.safeTransferFrom(accounts[0].address, contract.address, 0, {"from": accounts[0]})

    def test_safe_transfer_approved(self, contract):
        contract.approve(accounts[4].address, 0, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[1].address, 0, {"from": accounts[4]})
        assert(
            contract.ownerOf(0) == accounts[1].address and
            contract.balanceOf(accounts[1].address) == 1 and
            contract.getApproved(0) == f"0x{bytes(20).hex()}"
        )

    def test_safe_transfer_from_owner(self, contract):
        contract.safeTransferFrom(accounts[1].address, accounts[0].address, 0, {"from": accounts[1]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1 and
            contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True
        )

    def test_safe_transfer_from_approved_for_all(self, contract):
        contract.safeTransferFrom(accounts[0].address, accounts[8].address, 0, {"from": accounts[6]})
        assert(
            contract.ownerOf(0) == accounts[8].address and
            contract.balanceOf(accounts[8].address) == 1
        )

class TestERC721CreatorFuse:
    def test_mint_shatter_fuse(self, contract):
        tx1 = contract.mint("test/", {"from": accounts[0]})
        tx2 = contract.shatter(50, {"from": accounts[0]})
        tx3 = contract.fuse({"from": accounts[0]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            len(tx1.events) == 1 and
            len(tx2.events) == 52 and # 50 mints, 1 burn, 1 Shatter
            len(tx3.events) == 52 and # 50 burns, 1 mint, 1 Fuse
            contract.balanceOf(accounts[0].address) == 1
        )

    def test_mint_again(self, contract):
        with reverts("Already minted the first piece"):
            contract.mint("test/", {"from": accounts[0]})

    def test_approve_token_0(self, contract):
        tx = contract.approve(accounts[5].address, 0, {"from": accounts[0]})
        assert(
            contract.getApproved(0) == accounts[5].address and
            tx.events["Approval"]["owner"] == accounts[0].address and
            tx.events["Approval"]["approved"] == accounts[5].address and
            tx.events["Approval"]["tokenId"] == 0
        )
    
    def test_approve_nonexistent_token(self, contract):
        with reverts("ERC721: invalid token ID"):
            contract.approve(accounts[5].address, 1, {"from": accounts[0]})

    def test_approve_non_owner_of_token(self, contract):
        with reverts("ERC721: approve caller is not token owner or approved for all"):
            contract.approve(accounts[5].address, 0, {"from": accounts[5]})

    def test_approval_for_all(self, contract):
        contract.setApprovalForAll(accounts[6].address, True, {"from": accounts[0]})
        assert contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True

    def test_approve_if_approved_for_all(self, contract):
        contract.approve(accounts[4].address, 0, {"from": accounts[6]})

    def test_transfer_not_owner_or_approved(self, contract):
        with reverts("ERC721: caller is not token owner or approved"):
            contract.transferFrom(accounts[0].address, accounts[7].address, 0, {"from": accounts[7]})

    def test_transfer_approved(self, contract):
        contract.transferFrom(accounts[0].address, accounts[1].address, 0, {"from": accounts[4]})
        assert(
            contract.ownerOf(0) == accounts[1].address and
            contract.balanceOf(accounts[1].address) == 1 and
            contract.getApproved(0) == f"0x{bytes(20).hex()}"
        )

    def test_transfer_from_owner(self, contract):
        contract.transferFrom(accounts[1].address, accounts[0].address, 0, {"from": accounts[1]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1 and
            contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True
        )

    def test_transfer_from_approved_for_all(self, contract):
        contract.transferFrom(accounts[0].address, accounts[8].address, 0, {"from": accounts[6]})
        assert(
            contract.ownerOf(0) == accounts[8].address and
            contract.balanceOf(accounts[8].address) == 1
        )

    def test_transfer_owner_again(self, contract):
        contract.transferFrom(accounts[8].address, accounts[0].address, 0, {"from": accounts[8]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1
        )

    def test_safe_transfer_not_owner_or_approved(self, contract):
        with reverts("ERC721: caller is not token owner or approved"):
            contract.safeTransferFrom(accounts[0].address, accounts[7].address, 0, {"from": accounts[7]})

    def test_safe_transfer_bad_contract(self, contract):
        with reverts("ERC721: transfer to non ERC721Receiver implementer"):
            contract.safeTransferFrom(accounts[0].address, contract.address, 0, {"from": accounts[0]})

    def test_safe_transfer_approved(self, contract):
        contract.approve(accounts[4].address, 0, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[1].address, 0, {"from": accounts[4]})
        assert(
            contract.ownerOf(0) == accounts[1].address and
            contract.balanceOf(accounts[1].address) == 1 and
            contract.getApproved(0) == f"0x{bytes(20).hex()}"
        )

    def test_safe_transfer_from_owner(self, contract):
        contract.safeTransferFrom(accounts[1].address, accounts[0].address, 0, {"from": accounts[1]})
        assert(
            contract.ownerOf(0) == accounts[0].address and
            contract.balanceOf(accounts[0].address) == 1 and
            contract.isApprovedForAll(accounts[0].address, accounts[6].address) == True
        )

    def test_safe_transfer_from_approved_for_all(self, contract):
        contract.safeTransferFrom(accounts[0].address, accounts[8].address, 0, {"from": accounts[6]})
        assert(
            contract.ownerOf(0) == accounts[8].address and
            contract.balanceOf(accounts[8].address) == 1
        )

class TestTokenURI:
    def test_token_uri_init(self, contract):
        contract.mint("newURI/", {"from": accounts[0]})
        assert contract.tokenURI(0) == "newURI/0"

    def test_shatter(self, contract):
        contract.shatter(100, {"from": accounts[0]})
        uri_tf = True
        for i in range(1, 101):
            uri_tf = uri_tf and contract.tokenURI(i) == f"newURI/{i}"
        assert uri_tf

    def test_set_base_uri(self, contract):
        contract.setBaseURI("newerURI/", {"from": accounts[0]})
        uri_tf = True
        for i in range(1, 101):
            uri_tf = uri_tf and contract.tokenURI(i) == f"newerURI/{i}"
        assert uri_tf

    def test_fuse(self, contract):
        contract.fuse({"from": accounts[0]})
        assert contract.tokenURI(0) == "newerURI/0"

class TestTokenURIOneOfOne:
    def test_token_uri_init(self, contract):
        contract.mint("newURI/", {"from": accounts[0]})
        assert contract.tokenURI(0) == "newURI/0"

    def test_shatter(self, contract):
        contract.shatter(1, {"from": accounts[0]})
        assert contract.tokenURI(0) == "newURI/0"

    def test_set_base_uri(self, contract):
        contract.setBaseURI("newerURI/", {"from": accounts[0]})
        assert contract.tokenURI(0) == "newerURI/0"

class TestShatterConstructor:

    def test_zero_min_shatter(self):
        contract = ShatterV1.deploy("SH", "SH", accounts[1].address, 750, accounts[1].address, 0, 100, 0, {"from": accounts[0]})
        assert contract.minShatters() == 1
