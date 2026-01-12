"use client";

import {
    LiveKitRoom,
    VideoConference,
    GridLayout,
    ParticipantTile,
    RoomAudioRenderer,
    ControlBar,
    useTracks,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useEffect, useState } from "react";
import { Track } from "livekit-client";

interface LiveKitRoomProps {
    roomName: string;
    username: string;
}

export default function LiveKitComponent({ roomName, username }: LiveKitRoomProps) {
    const [token, setToken] = useState("");

    useEffect(() => {
        (async () => {
            try {
                // เรียก NestJS API เพื่อขอ Token
                const resp = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL}/livekit/token?room=${roomName}&username=${username}`
                );
                const data = await resp.json();
                setToken(data.token);
            } catch (e) {
                console.error("Failed to fetch token:", e);
            }
        })();
    }, [roomName, username]);

    if (token === "") {
        return <div className="flex h-screen items-center justify-center">Loading...</div>;
    }

    return (
        <LiveKitRoom
            video={true}
            audio={true}
            token={token}
            serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
            data-lk-theme="default"
            style={{ height: "100vh" }}
            onDisconnected={() => {
                // เมื่อวางสาย ให้ redirect หรือทำอย่างอื่น
                window.location.href = "/";
            }}
        >
            {/* ใช้ UI สำเร็จรูปของ LiveKit (เหมือน Zoom) */}
            <VideoConference />

            {/* สิ่งนี้จำเป็นเพื่อจัดการเสียงในห้อง */}
            <RoomAudioRenderer />
        </LiveKitRoom>
    );
}