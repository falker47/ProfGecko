import Header from "@/components/layout/Header";
import ChatContainer from "@/components/chat/ChatContainer";

export default function Home() {
  return (
    <main className="flex h-dvh flex-col">
      <Header />
      <ChatContainer />
    </main>
  );
}
