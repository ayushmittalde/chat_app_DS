from bullyalgo import CommunityLayer
import time

def testcase1():
    """
    Normal execution : LEADER FAILURE -> ELECTION -> RESPONSE ->COOD -> LEADER
    """
    obj=CommunityLayer()
    obj.test_selfid("1")
    obj.leaderalive()
    obj.start()
    obj.leaderfailure()
    # received election message
    obj.test_sendresponsemsg("3")
    # shoul be in co-od state
    obj.test_sendcoordinatoremsg("5")
    # should move to idle state
    time.sleep(10)
    obj.stop()

def testcase2():
    """
    Test decription : 
    This tests that election only responds to the election message of lower ids. response of higher ids and co-ordinator of higher ids.
    Self ID : 2 ->heartbeat Failure ->ELECTION (3) ->ELECTION(1) ->RESPONSE(1)->RESPONSE(3)->COOD(1)->COOD(5) 
    """
    obj=CommunityLayer()
    obj.test_selfid("2")
    obj.leaderalive()
    obj.start()
    obj.leaderfailure()
    # Broadcast election message election message
    time.sleep(2) # close to timeout
    obj.test_sendelectionmsg("3") # should be ignored
    time.sleep(1)
    obj.test_sendelectionmsg("1") # should be processed

    obj.test_sendresponsemsg("1") # should be ignored
    time.sleep(1)
    obj.test_sendresponsemsg("3") # should be processed
    # shoul be in co-od stateclear

    obj.test_sendcoordinatoremsg("1")
    time.sleep(1)
    obj.test_sendcoordinatoremsg("5")
    # should move to idle state
    time.sleep(7)
    obj.stop()


def testcase3():
    """
    Timeout testing for WAITING response state
    """
    obj=CommunityLayer()
    obj.test_selfid("2")
    obj.leaderalive()
    obj.start()
    obj.leaderfailure()
    # Broadcast election message election message
    obj.test_sendcoordinatoremsg("1")   # should be ignored
    time.sleep(1)
    obj.test_sendcoordinatoremsg("2")   # should be ignored , should lead to timeout, and declare itself as leader

    time.sleep(7)
    obj.stop()

def testcase4():
    """
    Checking CO-OD message of higher and lower id in waiting response state 
    """
    obj=CommunityLayer()
    obj.test_selfid("2")
    obj.leaderalive()
    obj.start()
    obj.leaderfailure()
    # Broadcast election message election message
    #WAITING RESPONSE
    obj.test_sendcoordinatoremsg("1")   # should be ignored
    time.sleep(1)
    obj.test_sendcoordinatoremsg("2")   # should be ignored , should lead to timeout
    obj.test_sendcoordinatoremsg("3")   # should lead to leader
    time.sleep(7)
    obj.stop()

def testcase5():    # waiting co-od
    """
    checking that messages are correctly processed of lower ids and higher ids in CO-OD waiting state
    """
    obj=CommunityLayer()
    obj.test_selfid("2")
    obj.leaderalive()
    obj.start()
    obj.leaderfailure()
    # received election message
    obj.test_sendresponsemsg("3")
    # shoul be in co-od state

    obj.test_sendelectionmsg("3") # should be ignored
    time.sleep(1)
    obj.test_sendelectionmsg("1") # should be processed
    obj.test_sendelectionmsg("2") # should not be processed
    obj.test_sendelectionmsg("1") # should be processed
    obj.test_sendelectionmsg("4") # should not be processed

    obj.test_sendresponsemsg("1") # should be ignored
    time.sleep(1)
    obj.test_sendresponsemsg("3") # message processed but not done anything
    obj.test_sendresponsemsg("4") # message processed but not done anything
    obj.test_sendresponsemsg("5") # message processed but not done anything
    obj.test_sendresponsemsg("2") # should be ignored
    # shoul be in co-od state
    
    obj.test_sendcoordinatoremsg("1")   # should be ignored
    obj.test_sendcoordinatoremsg("1")   # should be ignored
    time.sleep(1)
    obj.test_sendcoordinatoremsg("2")   # should be ignored 

    obj.test_sendcoordinatoremsg("5")   # should be processed
    # should move to idle state
    time.sleep(10)
    obj.stop()

def testcase6():
    """
    RESPONSE TO ELECTION message in CO-OD state
    """
    obj=CommunityLayer()
    obj.test_selfid("2")
    obj.leaderalive()
    obj.start()
    obj.leaderfailure() # start election message

    obj.test_sendresponsemsg("3")   # move to COOD
    obj.test_sendelectionmsg("1")   # respond to election while waiting for cod
    # shoul be in co-od state
    obj.test_sendcoordinatoremsg("5")   # should select new leader
    # should move to idle state
    time.sleep(10)
    obj.stop()

def testcase7():
    """
    IDLE -> RESPONSE IGNORED -> COORDINATOR IGNORED from self
    """
    obj=CommunityLayer()
    obj.test_selfid("1")
    obj.leaderalive()
    obj.start()
    obj.test_sendresponsemsg("3")   # should be ignored
    obj.test_sendcoordinatoremsg("1")   # should be ignored
    time.sleep(10)
    obj.stop()

def testcase8():
    """
    IDLE -> IGNORE RESPONSE message -> COOD MESSAGE received ->NEW LEADER
    """
    obj=CommunityLayer()
    obj.test_selfid("1")
    obj.leaderalive()
    obj.start()
    obj.test_sendresponsemsg("3")   # should be ignored
    obj.test_sendcoordinatoremsg("5")   # should lead to new leader
    time.sleep(10)
    obj.stop()

def testcase9():
    """
    Receiving ELECTION message in IDLE state both from a lower Id and a higher ID
    """
    obj=CommunityLayer()
    obj.test_selfid("3")
    obj.leaderalive()
    obj.start()
    obj.test_sendelectionmsg("1")   # Should respond with a RESPONSE and START a new ELECTION
    obj.test_sendresponsemsg("4")   # Should be processed and since no co-od message after this threfore should lead to timeout -> new election -> declare itself as leader
    time.sleep(10)  # Found bug

def testcase10():
    """
    Receiving COORDINATOR message in IDLE state both from a lower Id and a higher ID
    """
    obj=CommunityLayer()
    obj.test_selfid("3")
    obj.leaderalive()
    obj.start()
    obj.test_sendcoordinatoremsg("4")   #Should change leader to 4
    time.sleep(1)
    obj.test_sendcoordinatoremsg("2")   # Should result in a new election
    time.sleep(10)  # Found bug

