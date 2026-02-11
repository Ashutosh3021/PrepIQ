import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const pathname = usePathname();

  // Navigation items as specified in the spec
  const navItems = [
    { name: 'My Subjects', icon: '📚', path: '/dashboard', badge: '3' },
    { name: 'Predictions', icon: '🔮', path: '/predictions' },
    { name: 'Study Buddy', icon: '🤖', path: '/chat', badge: '5' },
    { name: 'Mock Tests', icon: '📝', path: '/tests' },
    { name: 'Important Questions', icon: '🎯', path: '/questions' },
    { name: 'Trend Analysis', icon: '📊', path: '/analysis' },
    { name: 'Settings', icon: '⚙️', path: '/settings' },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div 
        className={`bg-white shadow-md transition-all duration-300 ${
          sidebarOpen ? 'w-60' : 'w-20'
        }`}
      >
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            {sidebarOpen && <h1 className="text-xl font-bold">PrepIQ</h1>}
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1 rounded hover:bg-gray-100"
            >
              {sidebarOpen ? '«' : '»'}
            </button>
          </div>
        </div>
        
        <nav className="mt-4">
          <ul>
            {navItems.map((item, index) => (
              <li key={index}>
                <Link
                  href={item.path}
                  className={`flex items-center px-4 py-3 ${
                    pathname === item.path
                      ? 'bg-teal-100 text-teal-700 border-r-2 border-teal-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <span className="text-lg mr-3">{item.icon}</span>
                  {sidebarOpen && (
                    <span className="flex-1">
                      {item.name}
                      {item.badge && (
                        <span className="ml-2 bg-teal-500 text-white text-xs rounded-full px-2 py-0.5">
                          {item.badge}
                        </span>
                      )}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        
        <div className="absolute bottom-0 w-60 p-4 border-t">
          <div className="mb-4">
            <label className="flex items-center cursor-pointer">
              <input type="checkbox" className="mr-2" />
              <span>Dark Mode</span>
            </label>
          </div>
          
          <button className="w-full mb-2 py-2 px-4 bg-gray-100 rounded hover:bg-gray-200 text-sm">
            Help & Feedback
          </button>
          
          <button className="w-full py-2 px-4 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm">
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navigation Bar */}
        <header className="bg-white shadow-sm">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center">
              <button 
                className="md:hidden mr-4 text-gray-600"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                ☰
              </button>
              <h2 className="text-xl font-semibold">Dashboard</h2>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search subjects, papers..."
                  className="border rounded-full py-2 px-4 pl-10 w-64 focus:outline-none focus:ring-2 focus:ring-teal-300"
                />
                <span className="absolute left-3 top-2.5">🔍</span>
              </div>
              
              <div className="relative">
                <button className="p-2 rounded-full hover:bg-gray-100 relative">
                  🔔
                  <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    3
                  </span>
                </button>
              </div>
              
              <div className="flex items-center">
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-semibold">
                  U
                </div>
                <span className="ml-2 hidden md:inline">Welcome</span>
              </div>
              
              <button className="p-2 rounded-full hover:bg-gray-100">⚙️</button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-4">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;