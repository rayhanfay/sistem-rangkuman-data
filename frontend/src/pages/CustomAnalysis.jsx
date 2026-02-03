import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useMcp } from '../contexts/McpProvider';
import { useToast } from '../contexts/ToastContext';
import apiService from '../services/api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import LoadingOverlay from '../components/common/LoadingOverlay';
import { Send, Bot, User } from 'lucide-react';

const CustomAnalysis = () => {
    const [messages, setMessages] = useState([
        { sender: 'ai', text: 'Halo! Silakan ajukan pertanyaan mengenai data aset Anda.' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false); 
    const [isPageLoading, setIsPageLoading] = useState(true); 
    const [availableTools, setAvailableTools] = useState([]);
    const [availableResources, setAvailableResources] = useState([]); 

    const { service: mcpService, status: mcpStatus } = useMcp();
    const { showToast } = useToast();
    const chatEndRef = useRef(null);

    useEffect(() => {
        if (mcpStatus !== 'connected') return;

        const unsubscribe = mcpService.on('analysis/progress', (progress) => {
            if (progress.status === 'completed') {
                setIsLoading(false);
                setMessages(prev => [...prev, { sender: 'ai', text: `Analisis selesai. Sekarang Anda bisa mengajukan pertanyaan spesifik mengenai hasil analisis ini.` }]);
                showToast(progress.message, 'success');
            } else if (progress.status === 'error') {
                setIsLoading(false);
                setMessages(prev => [...prev, { sender: 'ai', text: `Maaf, terjadi kesalahan saat analisis: ${progress.message}` }]);
                showToast(progress.message, 'error');
            }
        });

        return () => unsubscribe();
    }, [mcpService, mcpStatus, showToast]);

    useEffect(() => {
        if (mcpStatus !== 'connected') return;
        const fetchPrerequisites = async () => {
            try {
                const [toolsResult, resourcesResult] = await Promise.all([
                    mcpService.call('tools/list', {}),
                    mcpService.call('resources/list', {})
                ]);
                setAvailableTools(toolsResult.tools || []);
                setAvailableResources(resourcesResult.resources || []);
            } catch (error) {
                showToast(error.message || 'Gagal memuat prasyarat analisis.', 'error');
            } finally {
                setIsPageLoading(false); 
            }
        };
        fetchPrerequisites();
    }, [mcpService, mcpStatus, showToast]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = useCallback(async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading || mcpStatus !== 'connected') return;

        const userPrompt = input;
        const newMessages = [...messages, { sender: 'user', text: userPrompt }];
        setMessages(newMessages);
        setInput('');
        setIsLoading(true);

        try {
            const choiceResult = await apiService.getToolChoice(userPrompt, availableTools, newMessages, availableResources);
            const toolChoice = JSON.parse(choiceResult.tool_choice);

            if (!toolChoice.tool_name || toolChoice.tool_name === "tidak_ada_tool") {
                throw new Error("Maaf, saya tidak yakin tindakan apa yang harus diambil untuk permintaan tersebut.");
            }
            
            setMessages(prev => [...prev, { sender: 'ai', text: `Baik, saya akan menggunakan tool '${toolChoice.tool_name}' untuk mencari informasi...` }]);

            if (toolChoice.tool_name === 'trigger_analysis') {
                // Tambahkan pesan sistem agar user tahu apa yang terjadi
                setMessages(prev => [...prev, { 
                    sender: 'ai', 
                    text: `Saya akan menjalankan pembaruan analisis Dashboard untuk Anda. Silakan lihat progresnya pada indikator di atas.` 
                }]);

                mcpService.call('tools/call', {
                    name: toolChoice.tool_name,
                    arguments: toolChoice.arguments
                });
                
                // PENTING: Matikan loading karena trigger_analysis tidak menunggu respon summarize
                setIsLoading(false); 
            } else {
                const toolExecutionResult = await mcpService.call('tools/call', {
                    name: toolChoice.tool_name,
                    arguments: toolChoice.arguments
                });

                setMessages(prev => [...prev, { sender: 'ai', text: `Data diterima. Sedang menyiapkan jawaban...` }]);
                const finalResult = await apiService.summarizeResult(
                    userPrompt,
                    JSON.stringify(toolExecutionResult.content),
                    newMessages
                );
                
                setMessages(prev => [...prev, { sender: 'ai', text: finalResult.summary }]);
                setIsLoading(false); 
            }

        } catch (error) {
            const friendlyErrorMessage = error.message || "Maaf, terjadi kesalahan saat memproses permintaan Anda.";
            setMessages(prev => [...prev, { sender: 'ai', text: friendlyErrorMessage }]);
            showToast(friendlyErrorMessage, 'error');
            setIsLoading(false); 
        }
    }, [isLoading, mcpStatus, messages, availableTools, availableResources, input, mcpService, showToast]);

    if (isPageLoading) {
        return <LoadingOverlay />;
    }

    return (
        <div className="flex flex-col h-[calc(100vh-5rem)]">
            <div>
                <h1 className="text-3xl font-bold">Analisis Kustom (Percakapan)</h1>
                <p className="text-text-secondary mt-1 mb-4">
                    Ajukan pertanyaan dalam bahasa alami untuk berinteraksi dengan data aset Anda secara cerdas.
                </p>
            </div>
            <Card className="flex-grow flex flex-col">
                <Card.Content className="flex-grow overflow-y-auto p-4 space-y-4">
                    {messages.map((msg, index) => (
                        <div key={index} className={`flex items-start gap-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                            {msg.sender === 'ai' && <Bot className="h-8 w-8 text-brand-blue flex-shrink-0" />}
                            <div className={`p-3 rounded-lg max-w-2xl ${msg.sender === 'ai' ? 'bg-gray-100' : 'bg-brand-blue text-white'}`}>
                                <pre className="whitespace-pre-wrap font-sans text-sm">{msg.text}</pre>
                            </div>
                            {msg.sender === 'user' && <User className="h-8 w-8 text-gray-600 flex-shrink-0" />}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-start gap-3">
                            <Bot className="h-8 w-8 text-brand-blue flex-shrink-0" />
                            <div className="p-3 rounded-lg bg-gray-100 animate-pulse">
                                <p className="text-sm">Sedang berpikir...</p>
                            </div>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </Card.Content>
                <Card.Footer className="p-4 border-t">
                    <form onSubmit={handleSend} className="flex gap-2">
                        <Input
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            placeholder="Tanyakan sesuatu tentang aset, misal: 'aset rusak berat di area mana saja'"
                            disabled={isLoading}
                            className="flex-grow"
                        />
                        <Button type="submit" disabled={isLoading || !input.trim()} loading={isLoading}>
                            <Send className="h-5 w-5" />
                        </Button>
                    </form>
                </Card.Footer>
            </Card>
        </div>
    );
};

export default CustomAnalysis;