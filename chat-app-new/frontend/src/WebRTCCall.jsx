import React, { useEffect, useRef, useState } from 'react';
import io from 'socket.io-client';

const socket = io("your_server_endpoint");

const WebRTCCall = () => {
    const [localStream, setLocalStream] = useState(null);
    const [remoteStream, setRemoteStream] = useState(null);
    const [peerConnection, setPeerConnection] = useState(null);
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState(null);

    const localVideoRef = useRef(null);
    const remoteVideoRef = useRef(null);

    useEffect(() => {
        const pc = new RTCPeerConnection();
        setPeerConnection(pc);

        pc.onicecandidate = (event) => {
            if (event.candidate) {
                socket.emit('candidate', event.candidate);
            }
        };

        pc.ontrack = (event) => {
            setRemoteStream(event.streams[0]);
        };

        return () => {
            pc.close();
        };
    }, []);

    useEffect(() => {
        if (localStream) {
            localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, localStream);
            });
        }
    }, [localStream, peerConnection]);

    const startCall = async () => {
        setIsConnecting(true);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true
            });
            setLocalStream(stream);
            localVideoRef.current.srcObject = stream;

            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            socket.emit('offer', offer);
        } catch (err) {
            setError("Failed to access media devices: " + err.message);
        } finally {
            setIsConnecting(false);
        }
    };

    useEffect(() => {
        socket.on('offer', async (offer) => {
            if (peerConnection) {
                await peerConnection.setRemoteDescription(offer);
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                socket.emit('answer', answer);
            }
        });

        socket.on('answer', (answer) => {
            if (peerConnection) {
                peerConnection.setRemoteDescription(answer);
            }
        });

        socket.on('candidate', (candidate) => {
            if (peerConnection) {
                peerConnection.addIceCandidate(candidate);
            }
        });

        return () => socket.off();
    }, [peerConnection]);

    useEffect(() => {
        if (remoteStream) {
            remoteVideoRef.current.srcObject = remoteStream;
        }
    }, [remoteStream]);

    return (
        <div>
            <h1>WebRTC Call</h1>
            {error && <p>{error}</p>}
            <video ref={localVideoRef} autoPlay muted></video>
            <video ref={remoteVideoRef} autoPlay></video>
            <button onClick={startCall} disabled={isConnecting}>Start Call</button>
        </div>
    );
};

export default WebRTCCall;