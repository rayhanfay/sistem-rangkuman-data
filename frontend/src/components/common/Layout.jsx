import React, { useState } from 'react';
import Sidebar from './Sidebar';
import { Menu } from 'lucide-react';

const Layout = ({ children }) => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    return (
        <div className="flex h-screen bg-background">
            <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />

            <div className="flex-1 flex flex-col overflow-hidden">
                
                <header className="md:hidden p-4 bg-white/80 backdrop-blur-sm z-10 flex items-center shadow-sm border-b">
                    <button 
                        onClick={() => setIsSidebarOpen(true)}
                        className="p-2 text-gray-600 hover:text-brand-blue"
                    >
                        <Menu size={24} />
                    </button>
                    <div className="flex-grow text-center">
                         <h1 className="text-lg font-semibold text-text-primary">PHR Analytics</h1>
                    </div>
                    <div className="w-8"></div> 
                </header>

                <main className="flex-1 overflow-x-hidden overflow-y-auto p-6">
                    <div className="page-content w-full">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Layout;