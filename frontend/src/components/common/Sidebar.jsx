import React from 'react';
import PropTypes from 'prop-types'; // Tambahkan ini
import { NavLink } from 'react-router-dom';
import { 
    LayoutDashboard, 
    History, 
    RefreshCcw, 
    Users, 
    LogOut, 
    BarChart3, 
    X, 
    Beaker, 
    Database 
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const Sidebar = ({ isOpen, setIsOpen }) => {
    const { user, logout } = useAuth();

    const navigationItems = [
        { path: '/', label: 'Dashboard', icon: LayoutDashboard },
        { path: '/custom-analysis', label: 'Analisis Kustom', icon: Beaker },
        { path: '/stats', label: 'Statistik Detail', icon: BarChart3 },
        { path: '/cycle', label: 'Siklus Aset', icon: RefreshCcw },
        { path: '/master-data', label: 'Master Data', icon: Database },
    ];

    if (user && user.role === 'admin') {
        navigationItems.push(
            { path: '/history', label: 'Riwayat Analisis', icon: History },
            { path: '/account-management', label: 'Manajemen Akun', icon: Users }
        );
    }

    const navLinkClasses = "flex items-center px-4 py-3 text-gray-300 rounded-lg transition-all duration-200";
    const activeNavLinkClasses = "bg-brand-blue text-white shadow-inner";

    return (
        <>
            <div 
                className={`fixed inset-0 bg-black/50 z-20 md:hidden transition-opacity ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
                onClick={() => setIsOpen(false)}
                onKeyDown={(e) => e.key === 'Escape' && setIsOpen(false)}
                role="button"
                tabIndex={isOpen ? 0 : -1}
                aria-label="Tutup sidebar"
            ></div>

            <aside className={`fixed top-0 left-0 h-screen w-64 bg-sidebar text-text-light flex flex-col shadow-lg z-30 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0`}>
                
                <div className="flex items-center justify-between p-4 border-b border-gray-700">
                    <div className="flex items-center space-x-3">
                        <img src="/images/logo.png" alt="Logo PHR" className="w-10 bg-white rounded-full p-1" />
                        <div>
                            <h1 className="text-md font-bold leading-tight">Data Summarization</h1>
                            <p className="text-xs text-gray-400">Pertamina Hulu Rokan</p>
                        </div>
                    </div>
                    <button onClick={() => setIsOpen(false)} className="p-2 text-gray-400 hover:text-white md:hidden" aria-label="Close menu">
                        <X size={20} />
                    </button>
                </div>
                
                <nav className="flex-1 px-4 py-6 space-y-2">
                    {navigationItems.map(({ path, label, icon: Icon }) => (
                        <NavLink
                            key={path}
                            to={path}
                            onClick={() => setIsOpen(false)}
                            className={({ isActive }) => `${navLinkClasses} ${isActive ? activeNavLinkClasses : 'hover:bg-gray-700'}`}
                            end={path === '/'}
                        >
                            <Icon size={20} className="mr-4 flex-shrink-0" />
                            <span className="text-sm font-medium">{label}</span>
                        </NavLink>
                    ))}
                </nav>

                <div className="p-4 border-t border-gray-700 space-y-3">
                    <div className="flex items-center gap-3">
                        <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 bg-brand-blue rounded-full text-white font-bold">
                            {user?.email?.[0]?.toUpperCase()}
                        </div>
                        <div className="min-w-0">
                            <p className="text-sm font-semibold text-white break-all" title={user?.email}>
                                {user?.email}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <p className="text-xs text-gray-400 capitalize">
                            {user?.role?.replace('_', ' ')}
                        </p>
                        <button
                            onClick={logout}
                            className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-md text-brand-red/80 hover:bg-brand-red/20 hover:text-brand-red transition-colors duration-200"
                            title="Logout"
                        >
                            <LogOut size={16} />
                            Logout
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
};

// Validasi Props
Sidebar.propTypes = {
    isOpen: PropTypes.bool.isRequired,
    setIsOpen: PropTypes.func.isRequired
};

export default Sidebar;