import LiveKitComponent from "@/components/LiveKitRoom";

// ใน Next.js App Router เราสามารถรับ searchParams ได้ใน Props
export default async function MeetingPage({
  searchParams,
}: {
  searchParams: Promise<{ room?: string; user?: string }>;
}) {
  const { room, user } = await searchParams;
  const roomName = room || "default-room";
  const username = user || `user-${Math.floor(Math.random() * 1000)}`;

  return (
    <main>
      {/* เรียกใช้ Client Component */}
      <LiveKitComponent roomName={roomName} username={username} />
    </main>
  );
}