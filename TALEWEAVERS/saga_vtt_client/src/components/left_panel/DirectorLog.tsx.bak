import { useRef, useState } from 'react';
import { useGameStore } from '../../store/useGameStore';

export function DirectorLog() {
    const chatLog = useGameStore((s) => s.chat_log);
    const uiLocked = useGameStore((s) => s.ui_locked);
    const addChatMessage = useGameStore((s) => s.addChatMessage);
    const [inputText, setInputText] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    const handleSend = () => {
        if (!inputText.trim() || uiLocked) return;
        addChatMessage({ sender: 'PLAYER', text: inputText.trim() });
        setInputText('');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const getSenderStyle = (sender: string) => {
        switch (sender) {
            case 'SYSTEM': return 'text-amber-400 font-semibold';
            case 'AI_DIRECTOR': return 'text-purple-300 font-semibold';
            case 'PLAYER': return 'text-zinc-100 font-semibold';
            default: return 'text-zinc-400';
        }
    };

    const getSenderIcon = (sender: string) => {
        switch (sender) {
            case 'SYSTEM': return '⚙';
            case 'AI_DIRECTOR': return '🎭';
            case 'PLAYER': return '⚔';
            default: return '•';
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="px-4 py-3 border-b border-zinc-800 flex-shrink-0">
                <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-zinc-400">
                    Director's Log
                </h2>
            </div>

            {/* Chat Messages */}
            <div
                ref={scrollRef}
                className="flex-grow overflow-y-auto px-4 py-3 space-y-3 scrollbar-thin"
            >
                {chatLog.map((msg, i) => (
                    <div key={i} className="group">
                        <div className={`text-xs mb-0.5 ${getSenderStyle(msg.sender)}`}>
                            <span className="mr-1.5">{getSenderIcon(msg.sender)}</span>
                            {msg.sender === 'AI_DIRECTOR' ? 'DIRECTOR' : msg.sender}
                        </div>
                        <p className={`text-sm leading-relaxed ${msg.sender === 'AI_DIRECTOR'
                                ? 'text-zinc-300 italic pl-4 border-l-2 border-purple-800/50'
                                : msg.sender === 'SYSTEM'
                                    ? 'text-amber-200/80 text-xs font-mono pl-4'
                                    : 'text-zinc-200 pl-4'
                            }`}>
                            {msg.text}
                        </p>
                    </div>
                ))}

                {/* Typing Indicator */}
                {uiLocked && (
                    <div className="flex items-center gap-2 pt-2">
                        <div className="flex gap-1">
                            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                        <span className="text-xs text-purple-400 italic">Director is narrating...</span>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="px-4 py-3 border-t border-zinc-800 flex-shrink-0">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={uiLocked ? 'Waiting for Director...' : 'Describe your action...'}
                        disabled={uiLocked}
                        className="flex-grow bg-zinc-800/60 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-purple-600 focus:ring-1 focus:ring-purple-600/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    />
                    <button
                        onClick={handleSend}
                        disabled={uiLocked || !inputText.trim()}
                        className="px-4 py-2 bg-purple-700 hover:bg-purple-600 disabled:bg-zinc-800 disabled:text-zinc-600 rounded-lg text-sm font-semibold transition-colors"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
}
