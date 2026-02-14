import React, { useEffect, useRef, useState } from 'react';
import { useDebugValue } from 'react';

const WebRTCCall = ({ socket, conversationId, remoteUserId, isInitiator, isVideo, onEnd }) => {
    const [remoteStream, setRemoteStream] = useState(null);
    const [connectionState, setConnectionState] = useState('connecting');
    const pcRef = useRef(new RTCPeerConnection({
        iceServers: [
            {urls: 'stun:stun.lgoogle.com:19302'},
            {urls: 'stun:stun1.l.google.com:19302'},
            {urls: 'stun:stun2.l.google.com:19302'}
        ],
    }));

    const debugMode = true;

    const logDebug = (...messages) => {
        if (debugMode) {
            console.debug('[DEBUG]:', ...messages);
        }
    };

    useEffect(() => {
        const handleICECandidate = event => {
            if (event.candidate) {
                socket.emit('ice-candidate', {
                    candidate: event.candidate,
                    conversationId,
                    remoteUserId,
                });
                logDebug('ICE candidate added:', event.candidate);
            }
        };

        const handleTrackEvent = event => {
            setRemoteStream(event.streams[0]);
            logDebug('Remote stream received:', event.streams[0]);
        };

        const handleConnectionStateChange = () => {
            setConnectionState(pcRef.current.connectionState);
            logDebug('Connection state changed:', pcRef.current.connectionState);

            if (pcRef.current.connectionState === 'disconnected') {
                alert('تم قطع الاتصال');
                onEnd();
            }
        };

        pcRef.current.onicecandidate = handleICECandidate;
        pcRef.current.ontrack = handleTrackEvent;
        pcRef.current.onconnectionstatechange = handleConnectionStateChange;

        // Request media permissions and start the connection
        const initializeConnection = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: isVideo, audio: true });
                if (isInitiator) {
                    stream.getTracks().forEach(track => pcRef.current.addTrack(track, stream));
                    const offer = await pcRef.current.createOffer();
                    await pcRef.current.setLocalDescription(offer);
                    socket.emit('offer', { offer, conversationId, remoteUserId });
                    logDebug('Offer sent:', offer);
                } else {
                    socket.on('offer', async ({ offer }) => {
                        await pcRef.current.setRemoteDescription(new RTCSessionDescription(offer));
                        stream.getTracks().forEach(track => pcRef.current.addTrack(track, stream));
                        const answer = await pcRef.current.createAnswer();
                        await pcRef.current.setLocalDescription(answer);
                        socket.emit('answer', { answer, conversationId, remoteUserId });
                        logDebug('Answer sent:', answer);
                    });
                }
                setRemoteStream(stream);
            } catch (error) {
                alert('خطأ في الحصول على إذن الوصول إلى الكاميرا والميكروفون');
                console.error('Error accessing media devices:', error);
            }
        };

        initializeConnection();

        return () => {
            pcRef.current.close();
            logDebug('Peer connection closed.');
        };
    }, [isInitiator, isVideo, socket, conversationId, remoteUserId, onEnd]);

    useDebugValue(connectionState);

    return (
        <div>
            {remoteStream && <video autoPlay playsInline ref={video => video && (video.srcObject = remoteStream)} />}
            <div>Connection state: {connectionState}</div>
            <button onClick={onEnd}>End Call</button>
        </div>
    );
};

export default WebRTCCall;
