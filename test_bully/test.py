from bullyalgo import CommunityLayer
import time

def testcase1():
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

testcase1()
