import { useRef, useState, useEffect } from 'react';
import { useGameStore } from '../../store/useGameStore';
import { useCharacterStore } from '../../store/useCharacterStore';

export function DirectorLog() {
    const chatLog = useGameStore((s) => s.chat_log);
    const uiLocked = useGameStore((s) => s.ui_locked);
    const campaignId = useGameStore((s) => s.activeCampaignId);
    const addChatMessage = useGameStore((s) => s.addChatMessage);
    const setUiLocked = useGameStore((s) => s.setUiLocked);
    const setPlayerVitals = useCharacterStore((s) => s.setPlayerVitals);

    const [inputText, setInputText] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to the newest message
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatLog]);

    const handleSend = async () => {
        if (!inputText.trim() || uiLocked || isProcessing) return;

        const actionText = inputText.trim();
        setInputText('');
        setIsProcessing(true);
        setUiLocked(true);

        // 1. Log the player's intent instantly
        addChatMessage({ sender: 'PLAYER', text: actionText });

        // 2. If we have a campaign ID, send to the Game Master Engine
        if (campaignId) {
            try {
                const res = await fetch('http://localhost:8000/api/campaign/action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ campaign_id: campaignId, player_input: actionText })
                });

                if (!res.ok) throw new Error("Game Master unreachable");
                const data = await res.json();

                // 3. Print the math log (Rules Engine)
                if (data.system_log) {
                    addChatMessage({ sender: 'SYSTEM', text: data.system_log.trim() });
                }

                // 4. Print the AI narration (The Director)
                if (data.narration) {
                    addChatMessage({ sender: 'AI_DIRECTOR', text: data.narration });
                }

                // 5. Update vitals if the API returned them
                if (data.updated_vitals) {
                    setPlayerVitals(data.updated_vitals);
                }
            } catch (err) {
                addChatMessage({ sender: 'SYSTEM', text: 'ERROR: Game Master Engine connection severed.' });
            }
        } else {
            // No campaign active — local mock response
            addChatMessage({ sender: 'SYSTEM', text: 'No campaign active. Start a campaign first.' });
        }

        setIsProcessing(false);
        setUiLocked(false);
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
            <div className="px-4 py-3 border-b border-zinc-800 flex-shrink-0 flex justify-between items-center">
                <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-zinc-400">
                    Director's Log
                </h2>
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${campaignId ? 'bg-green-500 animate-pulse' : 'bg-zinc-600'}`}
                        title={campaignId ? 'Engine Online' : 'No Campaign'} />
                </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-grow overflow-y-auto px-4 py-3 space-y-3 scrollbar-thin">
                {chatLog.length === 0 && (
                    <div className="text-center text-zinc-600 text-[10px] uppercase tracking-widest mt-10 font-mono">
                        Awaiting Director Initialization...
                    </div>
                )}

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
                {(uiLocked || isProcessing) && (
                    <div className="flex items-center gap-2 pt-2">
                        <div className="flex gap-1">
                            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                        <span className="text-xs text-purple-400 italic">Director is calculating...</span>
                    </div>
                )}

                <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
            <div className="px-4 py-3 border-t border-zinc-800 flex-shrink-0">
                <div className="flex flex-col gap-2">
                    <textarea
                        rows={2}
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={isProcessing ? 'Calculating...' : 'Describe your action...'}
                        disabled={uiLocked || isProcessing}
                        className="w-full bg-zinc-800/60 border border-zinc-700 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors resize-none"
                    />
                    <button
                        onClick={handleSend}
                        disabled={uiLocked || isProcessing || !inputText.trim()}
                        className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-black text-xs font-bold uppercase tracking-widest disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed transition-colors"
                    >
                        {isProcessing ? 'Calculating...' : 'Execute Action'}
                    </button>
                </div>
            </div>
        </div>
    );
}
