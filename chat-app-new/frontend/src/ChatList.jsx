import React, { useState } from 'react';

function ChatList() {
    const [contacts, setContacts] = useState([]);
    const [modalVisible, setModalVisible] = useState(false);

    const handleStartDirectFixed = (friend) => {
        // Logic to create a direct conversation with the friend
        const newConversation = { id: Date.now(), participants: [friend] };
        // Assuming conversations is a state variable that holds the list of conversations
        setConversations(prev => [...prev, newConversation]);
        setModalVisible(false); // Close the modal after adding
    };

    return (
        <div>
            {/* Modal and other UI components */}
            <button onClick={() => setModalVisible(true)}>Add Friend</button>
            {modalVisible && (
                <div className="modal">
                    {/* Modal content and friend selection here */}
                </div>
            )}
        </div>
    );
}

export default ChatList;