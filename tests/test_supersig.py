import pytest
from ape import accounts, project
from ape.types import HexBytes

@pytest.fixture()
def supersig(accounts):
    deployer = accounts[0]
    return deployer.deploy(project.supersig, [accounts[0], accounts[1], accounts[2]], 3)

@pytest.fixture()
def supersig_with_proposal(supersig, accounts):
    target = "0x000000000000000000000000000000000000dead"
    calldata = "0xbeaf"
    supersig.propose(1, target, calldata, sender=accounts[0])
    return supersig

@pytest.fixture()
def test_target_contract(accounts):
    deployer = accounts[0]
    return deployer.deploy(project.test_contract)

def test_init(supersig, accounts):
    assert supersig.minimum() == 3
    assert supersig.owners(0) == accounts[0]
    assert supersig.owners(1) == accounts[1]
    assert supersig.owners(2) == accounts[2]
    assert supersig == supersig.myself()

def test_proposal(supersig, accounts):
    target = "0x000000000000000000000000000000000000dead"
    calldata = "0xbeaf"
    supersig.propose(1, target, calldata, sender=accounts[0])
    assert supersig.proposals(1).target.lower() == target
    assert supersig.proposals(1).calldata == HexBytes(calldata)

def test_approval(supersig_with_proposal, accounts):
    supersig_with_proposal.approve(1, sender=accounts[0])
    assert supersig_with_proposal.approvals(1) == 1

def test_fail_approval_bad_caller(supersig_with_proposal, accounts):
    with pytest.raises(Exception):
        supersig_with_proposal.approve(1, sender=accounts[4])

def test_fail_approve_twice(supersig_with_proposal, accounts):
    ## approve once
    supersig_with_proposal.approve(1, sender=accounts[0])
    ## try to approve again
    with pytest.raises(Exception) as e:
        supersig_with_proposal.approve(1, sender=accounts[0])

def test_fail_approve_to_few_approvals(supersig_with_proposal, accounts):
    ## approve once
    supersig_with_proposal.approve(1, sender=accounts[0])
    ## try to approve again
    with pytest.raises(Exception) as e:
        supersig_with_proposal.execute(1, sender=accounts[1])

def test_execute(supersig, test_target_contract, accounts):
    calldata = "0x70a5aa210000000000000000000000000000000000000000000000000000000000000045"
    supersig.propose(2, test_target_contract, calldata, sender=accounts[0])

    ## Approve three times
    supersig.approve(2, sender=accounts[0])
    supersig.approve(2, sender=accounts[1])
    supersig.approve(2, sender=accounts[2])

    ## Execute
    supersig.execute(2, sender=accounts[0])

    ## Check that the proposal was executed
    assert test_target_contract.magic_number() == 0x45