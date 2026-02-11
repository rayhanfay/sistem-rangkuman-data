import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types'; // Tambahkan ini
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const UserMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);
  const navigate = useNavigate();
  const { logout, user } = useAuth(); 

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="user-menu-container" ref={menuRef}>
      {/* PERBAIKAN: Bungkus img dengan button agar interaktif secara asli */}
      <button
        type="button"
        className="user-icon-button" // Sesuaikan CSS jika perlu
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label="Buka menu pengguna"
        style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
      >
        <img
          src="/images/user.png"
          alt="Avatar Pengguna"
          className="user-icon"
        />
      </button>
      
      <div className={`dropdown-menu-custom ${isOpen ? 'show' : ''}`} role="menu">
        <div className="user-profile">
          <img src="/images/user.png" alt="User Profile" />
          <h6 className="text-sm font-medium text-gray-700 mb-0">Welcome</h6>
          <small className="text-xs text-gray-500">{user ? user.username : 'User'}</small>
        </div>
        
        <button className="btn-logout" onClick={handleLogout} role="menuitem">
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </div>
  );
};

export default UserMenu;