// WebRTCCall.jsx

import React, { useEffect, useRef, useState } from 'react';

const WebRTCCall = () => {
    const [remoteStream, setRemoteStream] = useState(null);
    const [localStream, setLocalStream] = useState(null);
    const peerConnectionRef = useRef(null);

    useEffect(() => {
        const initLocalStream = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                setLocalStream(stream);
                const videoElement = document.getElementById('localVideo');
                if (videoElement) videoElement.srcObject = stream;
            } catch (error) {
                console.error('Error accessing media devices.', error);
            }
        };

        initLocalStream();
    }, []);

    useEffect(() => {
        const peerConnection = new RTCPeerConnection();
        peerConnectionRef.current = peerConnection;

        const addTracksToPeerConnection = () => {
            localStream && localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, localStream);
            });
        };

        const handleTrackEvent = ({ streams }) => {
            setRemoteStream(streams[0]);
            const remoteVideoElement = document.getElementById('remoteVideo');
            if (remoteVideoElement) remoteVideoElement.srcObject = streams[0];
        };

        peerConnection.ontrack = handleTrackEvent;

        const handleICECandidate = (event) => {
            if (event.candidate) {
                console.log('New ICE candidate: ', event.candidate);
                // Send the candidate to the remote peer
            }
        };

        peerConnection.onicecandidate = handleICECandidate;

        const handleConnectionStateChange = () => {
            console.log('Connection State: ', peerConnection.connectionState);
            if (peerConnection.connectionState === 'failed') {
                console.error('Connection failed.');
            }
        };

        peerConnection.onconnectionstatechange = handleConnectionStateChange;

        addTracksToPeerConnection();

        return () => {
            peerConnection.close();
        };
    }, [localStream]);

    return (
        <div>
            <video id="localVideo" autoPlay muted></video>
            <video id="remoteVideo" autoPlay></video>
        </div>
    );
};

export default WebRTCCall;