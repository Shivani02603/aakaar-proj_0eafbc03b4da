```typescript
import { Inter } from 'next/font/google';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import SessionSidebar from '@/components/SessionSidebar';
import DocumentUploader from '@/components/DocumentUploader';
import ChatWindow from '@/components/ChatWindow';
import AuthGuard from '@/components/AuthGuard';
import { isAuthenticated, getUser, removeToken } from '@/lib/auth';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [user, setUser] = useState<{ name: string; avatar: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      if (!isAuthenticated()) {
        router.push('/login');
      } else {
        const userData = await getUser();
        setUser(userData);
      }
    };
    checkAuth();
  }, [router]);

  const handleLogout = () => {
    removeToken();
    router.push('/login');
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
  };

  return (
    <html lang="en" className={inter.className}>
      <body className="bg-gray-100 text-gray-900">
        <AuthGuard>
          <div className="flex flex-col h-screen">
            {/* Top Navigation Bar */}
            <header className="flex items-center justify-between bg-white shadow px-4 py-2">
              <h1 className="text-xl font-semibold">Aakaar Project</h1>
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleNewChat}
                  className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                  New Chat
                </button>
                {user && (
                  <div className="flex items-center space-x-2">
                    <img
                      src={user.avatar}
                      alt="User Avatar"
                      className="w-8 h-8 rounded-full"
                    />
                    <span>{user.name}</span>
                    <button
                      onClick={handleLogout}
                      className="text-red-500 hover:underline"
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </header>

            {/* Main Content */}
            <div className="flex flex-1 overflow-hidden">
              {/* Left Sidebar */}
              <aside className="w-64 bg-gray-200 border-r flex flex-col">
                <SessionSidebar
                  onSelectSession={(sessionId) => setActiveSessionId(sessionId)}
                />
                <DocumentUploader />
              </aside>

              {/* Right Main Area */}
              <main className="flex-1 overflow-y-auto">
                <ChatWindow sessionId={activeSessionId} />
              </main>
            </div>
          </div>
        </AuthGuard>
      </body>
    </html>
  );
}
```