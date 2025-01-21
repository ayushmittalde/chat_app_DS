from vectors import *
participants ={"1":1,"2":1, "3":0}
message1 = {
    "ordering_type": "APPLICATION",
    "content": "ayush",
    "vector_clock": {"1":1,"2":1, "3":0},
    "sender_uuid": "2"
}

message2 = {
    "ordering_type": "APPLICATION",
    "content": "mittal",
    "vector_clock": {"1":1,"2":0,"3":0},
    "sender_uuid": "1"
}

message3 = {
    "ordering_type": "APPLICATION",
    "content": "Ayush",
    "vector_clock": {"1":0,"2":0,"3":1},
    "sender_uuid": "3"
}

message4 = {
    "ordering_type": "APPLICATION",
    "content": "Mittal",
    "vector_clock": {"1":0,"2":0,"3":2},
    "sender_uuid": "3"
}
message5 = {
    "ordering_type": "APPLICATION",
    "content": "Good",
    "vector_clock": {"1":0,"2":0,"3":3},
    "sender_uuid": "3"
}

message2 = {
    "ordering_type": "APPLICATION",
    "content": "mittal",
    "vector_clock": {"1":1,"2":0,"3":0},
    "sender_uuid": "1"
}

message3 = {
    "ordering_type": "APPLICATION",
    "content": "Ayush",
    "vector_clock": {"1":0,"2":0,"3":1},
    "sender_uuid": "3"
}

def test1():
    """
    Test FIFO ordering from one node
    """
    participants ={"1":1,"2":1, "3":0}
    obj=VectorClockSystem("1",participants)
    obj.start()

    obj.handle_message(message5)
    obj.handle_message(message4)
    obj.handle_message(message3)

    #should deliever 3 4 and 5

def test2():
    """
    Test FIFO ordering from one node
    """
    participants ={"1":1,"2":1, "3":0}
    obj=VectorClockSystem("1",participants)
    obj.start()

    obj.handle_message(message5)
    obj.handle_message(message3)
    obj.handle_message(message4)

    #should deliever 3 4 and 5



def test3():
    """
    Checking independent messages
    """
    participants ={"1":1,"2":1, "3":0}
    obj=VectorClockSystem("1",participants)
    obj.start()

    obj.handle_message(message2)
    obj.handle_message(message3)
    #both should be printed

def test4():
    """
    Checking independent messages
    """
    participants ={"1":1,"2":1, "3":0}
    obj=VectorClockSystem("1",participants)
    obj.start()

    obj.handle_message(message3)
    obj.handle_message(message2)
    #both should be printed

def test5():
    """
    Checking causal order
    """
    participants ={"1":1,"2":1, "3":0}
    obj=VectorClockSystem("1",participants)
    obj.start()

    obj.handle_message(message1)
    obj.handle_message(message2)
    #both should be printed

import time

def test_concurrent_messages():
    """
    Test concurrent messages with interleaved dependencies
    """
    participants = {"1": 0, "2": 0, "3": 0}
    obj = VectorClockSystem("1", participants)
    obj.start()
    
    message_a = {"ordering_type": "APPLICATION", "content": "A", "vector_clock": {"1": 1, "2": 0, "3": 0}, "sender_uuid": "1"}
    message_b = {"ordering_type": "APPLICATION", "content": "B", "vector_clock": {"1": 0, "2": 1, "3": 0}, "sender_uuid": "2"}
    
    obj.handle_message(message_b)
    obj.handle_message(message_a)
    
    # Both should be delivered as they are independent

def test_hold_back_queue_processing():
    """
    Test processing of hold-back queue
    """
    participants = {"1": 0, "2": 0, "3": 0}
    obj = VectorClockSystem("1", participants)
    obj.start()
    
    message_x = {"ordering_type": "APPLICATION", "content": "X", "vector_clock": {"1": 2, "2": 0, "3": 0}, "sender_uuid": "1"}
    message_y = {"ordering_type": "APPLICATION", "content": "Y", "vector_clock": {"1": 1, "2": 0, "3": 0}, "sender_uuid": "1"}
    
    obj.handle_message(message_x)
    time.sleep(1)
    obj.handle_message(message_y)
    
    # Message Y should be delivered first, and then X

def test_out_of_order_delivery():
    """
    Test handling of messages arriving out of order
    """
    participants = {"1": 0, "2": 0, "3": 0}
    obj = VectorClockSystem("1", participants)
    obj.start()
    
    message_early = {"ordering_type": "APPLICATION", "content": "Early", "vector_clock": {"1": 1, "2": 0, "3": 0}, "sender_uuid": "1"}
    message_late = {"ordering_type": "APPLICATION", "content": "Late", "vector_clock": {"1": 2, "2": 0, "3": 0}, "sender_uuid": "1"}
    
    obj.handle_message(message_late)
    obj.handle_message(message_early)
    
    # Early should be delivered first

def test_empty_queue():
    """
    Test handling of empty message queue
    """
    participants = {"1": 0, "2": 0, "3": 0}
    obj = VectorClockSystem("1", participants)
    obj.start()
    
    time.sleep(1)
    assert obj.getcopy_hold_back_queue() == [], "Hold-back queue should be empty initially"

def test_multiple_dependencies():
    """
    Test causal dependencies across multiple nodes
    """
    participants = {"1": 0, "2": 0, "3": 0}
    obj = VectorClockSystem("1", participants)
    obj.start()
    
    msg1 = {"ordering_type": "APPLICATION", "content": "Msg1", "vector_clock": {"1": 1, "2": 0, "3": 0}, "sender_uuid": "1"}
    msg2 = {"ordering_type": "APPLICATION", "content": "Msg2", "vector_clock": {"1": 1, "2": 1, "3": 0}, "sender_uuid": "2"}
    msg3 = {"ordering_type": "APPLICATION", "content": "Msg3", "vector_clock": {"1": 1, "2": 1, "3": 1}, "sender_uuid": "3"}
    
    obj.handle_message(msg3)
    obj.handle_message(msg1)
    obj.handle_message(msg2)
    
    # Should deliver in order Msg1 -> Msg2 -> Msg3

def test_stress_hold_back_queue():
    """
    Stress test the hold-back queue with multiple FIFO and causal dependencies
    """
    participants = {"1": 0, "2": 0, "3": 0}
    obj = VectorClockSystem("1", participants)
    obj.start()
    
    messages = [
        {"ordering_type": "APPLICATION", "content": "M1", "vector_clock": {"1": 1, "2": 0, "3": 0}, "sender_uuid": "1"},
        {"ordering_type": "APPLICATION", "content": "M2", "vector_clock": {"1": 2, "2": 0, "3": 0}, "sender_uuid": "1"},
        {"ordering_type": "APPLICATION", "content": "M3", "vector_clock": {"1": 2, "2": 1, "3": 0}, "sender_uuid": "2"},
        {"ordering_type": "APPLICATION", "content": "M4", "vector_clock": {"1": 2, "2": 1, "3": 1}, "sender_uuid": "3"},
        {"ordering_type": "APPLICATION", "content": "M5", "vector_clock": {"1": 3, "2": 1, "3": 1}, "sender_uuid": "1"}
    ]
    
    obj.handle_message(messages[3])
    obj.handle_message(messages[4])
    obj.handle_message(messages[2])
    obj.handle_message(messages[1])
    obj.handle_message(messages[0])
    obj.handle_message(messages[0])

    time.sleep(4)


def test_stress_hold_back_queue2():
    """
    Stress test the hold-back queue with multiple FIFO and causal dependencies
    """
    participants = {"1": 0, "2": 0, "3": 0}
    obj = VectorClockSystem("1", participants)
    obj.start()
    
    messages = [
        {"ordering_type": "APPLICATION", "content": "M1", "vector_clock": {"1": 1, "2": 0, "3": 0}, "sender_uuid": "1"},
        {"ordering_type": "APPLICATION", "content": "M2", "vector_clock": {"1": 2, "2": 0, "3": 0}, "sender_uuid": "1"},
        {"ordering_type": "APPLICATION", "content": "M3", "vector_clock": {"1": 2, "2": 1, "3": 0}, "sender_uuid": "2"},
        {"ordering_type": "APPLICATION", "content": "M4", "vector_clock": {"1": 2, "2": 1, "3": 1}, "sender_uuid": "3"},
        {"ordering_type": "APPLICATION", "content": "M5", "vector_clock": {"1": 3, "2": 1, "3": 1}, "sender_uuid": "1"}
    ]
    
    obj.handle_message(messages[4])
    obj.handle_message(messages[3])
    obj.handle_message(messages[2])
    obj.handle_message(messages[1])
    obj.handle_message(messages[0])

    time.sleep(4)

test_stress_hold_back_queue2()




