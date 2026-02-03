import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../hooks/useAuth';
import { useMcp } from '../contexts/McpProvider';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import LoadingOverlay from '../components/common/LoadingOverlay';
import { Users, Plus, Edit, Trash2 } from 'lucide-react';
import ConfirmationModal from '../components/common/ConfirmationModal';
import Input from '../components/ui/Input';

const Modal = ({ isOpen, onClose, children }) => {
    if (!isOpen) return null;
    return ReactDOM.createPortal(
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md" shadow="xl">{children}</Card>
        </div>,
        document.getElementById('modal-root')
    );
};

const AccountManagement = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null); 
    const [formData, setFormData] = useState({ email: '', password: '' });
    const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
    const [userToDelete, setUserToDelete] = useState(null);
    
    const { showToast } = useToast();
    const { user: currentUser } = useAuth();
    const { service: mcpService, status: mcpStatus } = useMcp();

    const fetchUsers = useCallback(async () => {
        if (mcpStatus !== 'connected') return;
        setLoading(true);
        try {
            const result = await mcpService.call('tools/call', { name: 'get_all_users' });
            setUsers(result.content);
        } catch (error) {
            showToast(error.message || 'Gagal memuat daftar pengguna.', 'error');
        } finally {
            setLoading(false);
        }
    }, [mcpService, mcpStatus, showToast]);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const handleOpenModal = (user = null) => {
        setEditingUser(user);
        setFormData(user ? { email: user.email, password: '' } : { email: '', password: '' });
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setEditingUser(null);
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (mcpStatus !== 'connected') {
            showToast('Koneksi belum siap.', 'warning');
            return;
        }

        if (editingUser) {
            try {
                await mcpService.call('tools/call', {
                    name: 'update_user_email',
                    arguments: { user_id: editingUser.id, new_email: formData.email }
                });
                showToast('Email pengguna berhasil diperbarui.', 'success');
                fetchUsers();
                handleCloseModal();
            } catch (error) {
                showToast(`Gagal memperbarui email: ${error.message}`, 'error');
            }
        } 
        else {
            try {
                const payload = { ...formData, role: 'user' }; 
                await mcpService.call('tools/call', {
                    name: 'create_user',
                    arguments: payload
                });
                showToast('Pengguna baru berhasil dibuat.', 'success');
                fetchUsers();
                handleCloseModal();
            } catch (error) {
                showToast(`Gagal membuat pengguna: ${error.message}`, 'error');
            }
        }
    };
    
    const handleDeleteClick = (user) => {
        setUserToDelete(user);
        setIsConfirmModalOpen(true);
    };

    const confirmDelete = async () => {
        if (!userToDelete || mcpStatus !== 'connected') return;
        try {
            await mcpService.call('tools/call', {
                name: 'delete_user',
                arguments: { user_id: userToDelete.id }
            });
            showToast('Pengguna berhasil dihapus.', 'success');
            fetchUsers();
        } catch (error) {
            showToast(`Gagal menghapus: ${error.message}`, 'error');
        } finally {
            setIsConfirmModalOpen(false);
            setUserToDelete(null);
        }
    };

    if (loading) return <LoadingOverlay />;

    return (
        <>
            <ConfirmationModal
                isOpen={isConfirmModalOpen}
                onClose={() => setIsConfirmModalOpen(false)}
                onConfirm={confirmDelete}
                title="Konfirmasi Penghapusan"
                message={`Apakah Anda yakin ingin menghapus pengguna ${userToDelete?.email}?`}
            />
            <div className="space-y-6">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <h1 className="text-3xl font-bold">Manajemen Akun</h1>
                    <Button onClick={() => handleOpenModal()}>
                        <Plus className="mr-2" size={16} /> Tambah Pengguna Baru
                    </Button>
                </div>

                <Card>
                    <Card.Content className="p-0">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Aksi</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {users.map(user => (
                                        <tr key={user.id}>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{user.email}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">{user.role}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                                                <Button 
                                                    variant="ghost" 
                                                    size="sm" 
                                                    onClick={() => handleOpenModal(user)} 
                                                    disabled={user.email === currentUser?.email || user.role === 'admin'}
                                                    title={user.role === 'admin' ? 'Email admin tidak dapat diubah' : 'Edit Pengguna'}
                                                >
                                                    <Edit size={16} />
                                                </Button>
                                                <Button 
                                                    variant="danger" 
                                                    size="sm" 
                                                    onClick={() => handleDeleteClick(user)} 
                                                    disabled={user.email === currentUser?.email || user.role === 'admin'}
                                                    title={user.role === 'admin' ? 'Admin tidak dapat dihapus' : 'Hapus Pengguna'}
                                                >
                                                    <Trash2 size={16} />
                                                </Button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </Card.Content>
                </Card>
            </div>
            <Modal isOpen={isModalOpen} onClose={handleCloseModal}>
                <form onSubmit={handleSubmit} className="space-y-4 p-4">
                    <h2 className="text-xl font-bold">{editingUser ? 'Edit Email Pengguna' : 'Tambah Pengguna Baru'}</h2>
                    {editingUser 
                        ? <p className="text-sm text-gray-500">Anda akan mengubah email untuk: <span className="font-bold">{editingUser.email}</span></p> 
                        : <p className="text-sm text-gray-500">Pengguna baru akan otomatis dibuat dengan peran 'user'.</p>
                    }
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">{editingUser ? 'Email Baru' : 'Email'}</label>
                        <Input type="email" name="email" id="email" value={formData.email} onChange={handleChange} required />
                    </div>
                    {!editingUser && (
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                            <Input type="password" name="password" id="password" value={formData.password} onChange={handleChange} required />
                        </div>
                    )}
                    <div className="flex justify-end space-x-2 pt-4">
                        <Button type="button" variant="ghost" onClick={handleCloseModal}>Batal</Button>
                        <Button type="submit">{editingUser ? 'Simpan Perubahan' : 'Buat Pengguna'}</Button>
                    </div>
                </form>
            </Modal>
        </>
    );
};

export default AccountManagement;