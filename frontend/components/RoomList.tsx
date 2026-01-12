"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface Room {
    sid: string;
    name: string;
    numParticipants: number;
    creationTime: number;
}

export default function RoomList() {
    const router = useRouter();
    const [rooms, setRooms] = useState<Room[]>([]);
    const [loading, setLoading] = useState(true);
    const [username, setUsername] = useState("");
    const [newRoomName, setNewRoomName] = useState("");

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";

    useEffect(() => {
        fetchRooms();
        // Random username if not set
        setUsername(`guest-${Math.floor(Math.random() * 1000)}`);
    }, []);

    const fetchRooms = async () => {
        try {
            const res = await fetch(`${apiUrl}/livekit/rooms`);
            if (res.ok) {
                const data = await res.json();
                setRooms(data);
            }
        } catch (error) {
            console.error("Failed to fetch rooms:", error);
        } finally {
            setLoading(false);
        }
    };

    const joinRoom = (roomName: string) => {
        if (!username) return alert("Please enter a username");
        router.push(`/?room=${roomName}&user=${username}`);
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white p-4">
            <div className="w-full max-w-md bg-gray-900 rounded-lg p-6 shadow-xl border border-gray-800">
                <h1 className="text-2xl font-bold mb-6 text-center text-cyan-400">LiveKit Rooms</h1>

                {/* User Settings */}
                <div className="mb-6">
                    <label className="block text-sm text-gray-400 mb-2">Your Name</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="Enter your name"
                    />
                </div>

                {/* Create New Room */}
                <div className="mb-8 border-b border-gray-800 pb-6">
                    <label className="block text-sm text-gray-400 mb-2">Create New Room</label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={newRoomName}
                            onChange={(e) => setNewRoomName(e.target.value)}
                            className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                            placeholder="Room name"
                        />
                        <button
                            onClick={() => newRoomName && joinRoom(newRoomName)}
                            disabled={!newRoomName || !username}
                            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-bold py-2 px-4 rounded transition-colors"
                        >
                            Create
                        </button>
                    </div>
                </div>

                {/* Active Rooms List */}
                <div>
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-lg font-semibold text-gray-300">Active Rooms</h2>
                        <button onClick={fetchRooms} className="text-sm text-cyan-400 hover:text-cyan-300">Refresh</button>
                    </div>

                    {loading ? (
                        <p className="text-center text-gray-500">Loading rooms...</p>
                    ) : rooms.length === 0 ? (
                        <p className="text-center text-gray-600 italic py-4">No active rooms found.</p>
                    ) : (
                        <div className="space-y-3">
                            {rooms.map((room) => (
                                <div key={room.sid} className="flex items-center justify-between bg-gray-800 p-3 rounded hover:bg-gray-750 border border-gray-700">
                                    <div>
                                        <div className="font-medium text-white">{room.name}</div>
                                        <div className="text-xs text-gray-400">{room.numParticipants} participants</div>
                                    </div>
                                    <button
                                        onClick={() => joinRoom(room.name)}
                                        className="bg-green-600 hover:bg-green-500 text-white text-sm font-bold py-1.5 px-3 rounded transition-colors"
                                    >
                                        Join
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
