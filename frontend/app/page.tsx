import LiveKitComponent from "@/components/LiveKitRoom";
import RoomList from "@/components/RoomList";

// ใน Next.js App Router เราสามารถรับ searchParams ได้ใน Props
export default async function MeetingPage({
  searchParams,
}: {
  searchParams: Promise<{ room?: string; user?: string }>;
}) {
  const { room, user } = await searchParams;
  if (!room && !user) {
    return <RoomList />;
  }

  const finalRoomName = room || 'default-room';
  const finalUsername = user || `user-${Math.floor(Math.random() * 1000)}`;

  return (
    <main>
      <LiveKitComponent roomName={finalRoomName} username={finalUsername} />
    </main>
  );
}

// Add import at the top (this tool call handles the function body, I'll add import in next step if needed or assume it handles it)