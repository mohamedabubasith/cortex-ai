"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import ChatInterface, { ChatSession } from "@/components/ChatInterface";
import config from "@/lib/config";

interface Message {
    role: "user" | "assistant";
    content: string;
    thinking?: string;
    status?: string; // e.g. "Searching web for 'X'...", "Reading page..."
}

interface BackendSession {
    id: string;
    agent_id: string;
    created_at: string;
    messages: Array<{
        id: string;
        role: string;
        content: string;
        created_at: string;
    }>;
}

export default function PublicChatPage() {
    const params = useParams<{ shareId: string }>();
    const [messages, setMessages] = useState<Message[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [agentName, setAgentName] = useState<string>("Cortex AI");
    const [agentFirstMessage, setAgentFirstMessage] = useState<string>("");
    const [hasKB, setHasKB] = useState<boolean>(false);
    const [hasDB, setHasDB] = useState<boolean>(false);
    const [hasMCP, setHasMCP] = useState<boolean>(false);
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string>("");
    const [loading, setLoading] = useState(true);
    const [isValidAgent, setIsValidAgent] = useState(true);
    const [isSearchEnabled, setIsSearchEnabled] = useState(false);
    const [isKBEnabled, setIsKBEnabled] = useState(false);
    const [isDBEnabled, setIsDBEnabled] = useState(true);

    useEffect(() => {
        const initChat = async () => {
            if (params.shareId) {
                const searchParams = new URLSearchParams(window.location.search);
                const isNew = searchParams.get("new") === "true";

                // Check if user was on a specific session (from localStorage)
                const savedSessionId = localStorage.getItem(`currentSession_${params.shareId}`);

                // IMPORTANT: Fetch agent info FIRST to get first_message and KB status
                const firstMsg = await fetchAgentInfo();

                // Then load sessions (will use first_message if needed)
                // If isNew is true, we pass "new" to loadSessions to force a fresh state
                await loadSessions(isNew ? "new" : (savedSessionId || undefined), firstMsg);
            }
        };

        initChat();
    }, [params.shareId]);

    const fetchAgentInfo = async () => {
        try {
            const response = await fetch(`${config.apiV1Url}/chat/public/${params.shareId}`);
            if (response.ok) {
                const data = await response.json();
                setAgentName(data.name);
                setAgentFirstMessage(data.first_message || "");
                setHasKB(data.has_kb || false);
                setHasDB(data.has_db || false);
                setHasMCP(data.has_mcp || false);
                setIsValidAgent(true);
                return data.first_message || "";
            } else if (response.status === 404) {
                setIsValidAgent(false);
            }
        } catch (error) {
            console.error("Failed to fetch agent info", error);
        }
        return "";
    };

    // ... (rest of methods unchanged)



    const loadSessions = async (restoredSessionId?: string, firstMsgFromFetch?: string) => {
        try {
            const firstMessage = firstMsgFromFetch || agentFirstMessage;

            setLoading(true);
            const url = `${config.apiV1Url}/chat/public/${params.shareId}/sessions`;
            const response = await fetch(url);

            if (response.ok) {
                const backendSessions: BackendSession[] = await response.json();

                // Convert backend sessions to frontend format
                const sessionsList: ChatSession[] = backendSessions.map(s => ({
                    id: s.id,
                    title: s.messages && s.messages.length > 0
                        ? s.messages.find(m => m.role === "user")?.content.substring(0, 50) || "New chat"
                        : "New chat",
                    timestamp: new Date(s.created_at).getTime()
                }));

                setSessions(sessionsList);

                let sessionRestored = false;

                // Handle 'new' state explicitly
                if (restoredSessionId === "new") {
                    console.log("[loadSessions] Initializing 'new' chat state");
                    setMessages(firstMessage ? [{ role: "assistant", content: firstMessage }] : []);
                    setSessionId(null);
                    setCurrentSessionId("");
                    localStorage.setItem(`currentSession_${params.shareId}`, "new");
                    sessionRestored = true;
                }
                // If user was on a specific session (refresh), try to restore it
                else if (restoredSessionId) {
                    const inList = backendSessions.find(s => s.id === restoredSessionId);
                    if (inList) {
                        setCurrentSessionId(restoredSessionId);
                        setSessionId(restoredSessionId);
                        await loadSessionMessages(restoredSessionId, firstMessage);
                        sessionRestored = true;
                    } else {
                        const success = await loadSessionMessages(restoredSessionId, firstMessage);
                        if (success) {
                            setCurrentSessionId(restoredSessionId);
                            setSessionId(restoredSessionId);
                            sessionRestored = true;
                            setSessions(prev => [
                                { id: restoredSessionId, title: "Restored Session", timestamp: Date.now() },
                                ...prev
                            ]);
                        }
                    }
                }

                if (!sessionRestored) {
                    if (backendSessions.length > 0) {
                        const latest = backendSessions[0];
                        setCurrentSessionId(latest.id);
                        setSessionId(latest.id);
                        localStorage.setItem(`currentSession_${params.shareId}`, latest.id);
                        await loadSessionMessages(latest.id, firstMessage);
                    } else {
                        setMessages(firstMessage ? [{ role: "assistant", content: firstMessage }] : []);
                    }
                }
            } else {
                setMessages(firstMessage ? [{ role: "assistant", content: firstMessage }] : []);
            }
        } catch (error) {
            console.error("Failed to load sessions", error);
            const firstMessage = firstMsgFromFetch || agentFirstMessage;
            setMessages(firstMessage ? [{ role: "assistant", content: firstMessage }] : []);
        } finally {
            setLoading(false);
        }
    };

    const loadSessionMessages = async (sessionIdToLoad: string, firstMsgFromFetch?: string): Promise<boolean> => {
        try {
            const firstMessage = firstMsgFromFetch || agentFirstMessage;
            const response = await fetch(`${config.apiV1Url}/chat/public/${params.shareId}/sessions/${sessionIdToLoad}/messages`);

            if (response.ok) {
                const backendMessages = await response.json();
                const messagesList: Message[] = backendMessages.map((m: any) => ({
                    role: m.role as "user" | "assistant",
                    content: m.content,
                    thinking: m.thinking
                }));

                if (messagesList.length === 0 && firstMessage) {
                    setMessages([{ role: "assistant", content: firstMessage }]);
                } else {
                    setMessages(messagesList);
                }

                setLoading(false);
                return true;
            }
            return false;
        } catch (error) {
            console.error("Failed to load session messages", error);
            return false;
        }
    };

    const createNewSession = (firstMsgFromFetch?: string) => {
        const firstMessage = firstMsgFromFetch || agentFirstMessage;
        setCurrentSessionId("");
        setSessionId(null);
        setMessages(firstMessage ? [{ role: "assistant", content: firstMessage }] : []);
        localStorage.setItem(`currentSession_${params.shareId}`, "new");
    };

    const handleSelectSession = async (selectedSessionId: string) => {
        setCurrentSessionId(selectedSessionId);
        setSessionId(selectedSessionId);
        localStorage.setItem(`currentSession_${params.shareId}`, selectedSessionId);
        await loadSessionMessages(selectedSessionId);
    };

    const handleDeleteSession = async (sessionIdToDelete: string) => {
        try {
            const response = await fetch(
                `${config.apiV1Url}/chat/public/${params.shareId}/sessions/${sessionIdToDelete}`,
                { method: 'DELETE' }
            );

            if (response.ok) {
                if (sessionIdToDelete === currentSessionId) {
                    await loadSessions();
                } else {
                    setSessions(prev => prev.filter(s => s.id !== sessionIdToDelete));
                }
            }
        } catch (error) {
            console.error("Failed to delete session", error);
        }
    };

    const handleSendMessage = async (message: string) => {
        setIsStreaming(true);

        const userMessage = { role: "user" as const, content: message };
        setMessages((prev) => [...prev, userMessage, { role: "assistant", content: "" }]);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 180000);

        try {
            const response = await fetch(`${config.apiV1Url}/chat/public/${params.shareId}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message,
                    session_id: sessionId,
                    search_enabled: isSearchEnabled,
                    kb_enabled: isKBEnabled,
                    db_enabled: isDBEnabled
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = "";
            let assistantThinking = "";
            let assistantStatus = "";
            let isThinkingMode = false;
            let updateScheduled = false;

            const updateUI = () => {
                setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                        role: "assistant",
                        content: assistantMessage,
                        thinking: assistantThinking || undefined,
                        status: assistantStatus || undefined
                    };
                    return updated;
                });
                updateScheduled = false;
            };

            try {
                let streamBuffer = "";
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    streamBuffer += decoder.decode(value, { stream: true });

                    // Robust parsing loop
                    let lastProcessedLength = -1;
                    while (streamBuffer.length > 0 && streamBuffer.length !== lastProcessedLength) {
                        lastProcessedLength = streamBuffer.length;

                        if (isThinkingMode) {
                            const endIdx = streamBuffer.indexOf("</THINK>");
                            if (endIdx !== -1) {
                                assistantThinking += streamBuffer.substring(0, endIdx);
                                isThinkingMode = false;
                                streamBuffer = streamBuffer.substring(endIdx + 8);
                            } else {
                                // Check for partial </THINK> at the end
                                const lastTagStart = streamBuffer.lastIndexOf("</");
                                if (lastTagStart !== -1 && "</THINK>".startsWith(streamBuffer.substring(lastTagStart))) {
                                    assistantThinking += streamBuffer.substring(0, lastTagStart);
                                    streamBuffer = streamBuffer.substring(lastTagStart);
                                    break; // Wait for more data
                                } else {
                                    assistantThinking += streamBuffer;
                                    streamBuffer = "";
                                }
                            }
                        } else {
                            // Find earliest marker
                            const thinkStart = streamBuffer.indexOf("<THINK>");
                            const searchStart = streamBuffer.indexOf("<SEARCHING>");
                            const readStart = streamBuffer.indexOf("<READING>");
                            const kbStart = streamBuffer.indexOf("<KB_QUERY>");

                            const markers = [
                                { type: 'THINK', start: thinkStart, open: '<THINK>', close: '</THINK>' },
                                { type: 'SEARCHING', start: searchStart, open: '<SEARCHING>', close: '</SEARCHING>' },
                                { type: 'READING', start: readStart, open: '<READING>', close: '</READING>' },
                                { type: 'KB_QUERY', start: kbStart, open: '<KB_QUERY>', close: '</KB_QUERY>' }
                            ].filter(m => m.start !== -1).sort((a, b) => a.start - b.start);

                            if (markers.length > 0) {
                                const marker = markers[0];

                                // Process everything before marker
                                if (marker.start > 0) {
                                    const text = streamBuffer.substring(0, marker.start);
                                    assistantMessage += text;
                                    if (text.trim().length > 0) assistantStatus = "";
                                }

                                // Handle marker content
                                if (marker.type === 'THINK') {
                                    isThinkingMode = true;
                                    streamBuffer = streamBuffer.substring(marker.start + marker.open.length);
                                } else {
                                    const closeIdx = streamBuffer.indexOf(marker.close, marker.start + marker.open.length);
                                    if (closeIdx !== -1) {
                                        const content = streamBuffer.substring(marker.start + marker.open.length, closeIdx);
                                        if (marker.type === 'SEARCHING') assistantStatus = `Searching web for "${content}"...`;
                                        else if (marker.type === 'READING') assistantStatus = `Reading ${content}...`;
                                        else if (marker.type === 'KB_QUERY') assistantStatus = `Querying knowledge base...`;
                                        streamBuffer = streamBuffer.substring(closeIdx + marker.close.length);
                                    } else {
                                        // Wait for closing tag
                                        streamBuffer = streamBuffer.substring(marker.start);
                                        break;
                                    }
                                }
                            } else {
                                // No full tag start. Check for partial tag at end.
                                const lastOpen = streamBuffer.lastIndexOf("<");
                                if (lastOpen !== -1) {
                                    const potential = streamBuffer.substring(lastOpen);
                                    const possibleTags = ["<THINK>", "<SEARCHING>", "<READING>", "<KB_QUERY>"];
                                    if (possibleTags.some(tag => tag.startsWith(potential))) {
                                        assistantMessage += streamBuffer.substring(0, lastOpen);
                                        streamBuffer = potential;
                                        break;
                                    }
                                }

                                assistantMessage += streamBuffer;
                                if (streamBuffer.trim().length > 0) assistantStatus = "";
                                streamBuffer = "";
                            }
                        }
                    }

                    if (!updateScheduled) {
                        updateScheduled = true;
                        requestAnimationFrame(updateUI);
                    }
                }
            } finally {
                reader.releaseLock();
            }

            updateUI();

            const newSessionId = response.headers.get('x-session-id');
            if (!sessionId && newSessionId) {
                setSessionId(newSessionId);
                setCurrentSessionId(newSessionId);
                localStorage.setItem(`currentSession_${params.shareId}`, newSessionId);

                setSessions(prev => [
                    { id: newSessionId, title: message.substring(0, 50) || "New chat", timestamp: Date.now() },
                    ...prev
                ]);
            }

        } catch (error: any) {
            console.error("Failed to send message:", error);
            const errorMsg = error.name === 'AbortError' ? "Error: Request timed out." : `Error: ${error.message}`;
            setMessages((prev) => {
                const updated = [...prev];
                if (updated[updated.length - 1]?.role === "assistant" && !updated[updated.length - 1]?.content) {
                    updated[updated.length - 1] = { role: "assistant", content: errorMsg };
                } else {
                    updated.push({ role: "assistant", content: errorMsg });
                }
                return updated;
            });
        } finally {
            clearTimeout(timeoutId);
            setIsStreaming(false);
        }
    };

    const handleRetryMessage = async (messageIndex: number) => {
        let userMessageIndex = -1;
        for (let i = messageIndex - 1; i >= 0; i--) {
            if (messages[i].role === "user") {
                userMessageIndex = i;
                break;
            }
        }

        if (userMessageIndex !== -1) {
            const userMessage = messages[userMessageIndex].content;
            setMessages(prev => prev.slice(0, userMessageIndex));
            await new Promise(resolve => setTimeout(resolve, 100));
            await handleSendMessage(userMessage);
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-black">
                <div className="text-[#76B900] text-lg">Loading...</div>
            </div>
        );
    }

    if (!isValidAgent) {
        return (
            <div className="flex h-screen flex-col items-center justify-center bg-black text-white p-4">
                <h1 className="text-4xl font-bold text-[#76B900] mb-4">404</h1>
                <p className="text-xl mb-8 text-neutral-400">Agent not found or invalid chat link.</p>
                <a
                    href="/"
                    className="px-6 py-2 bg-[#76B900] text-black font-semibold rounded-lg hover:bg-[#86d100] transition-colors"
                >
                    Return Home
                </a>
            </div>
        );
    }

    return (
        <ChatInterface
            initialMessages={messages}
            onSendMessage={handleSendMessage}
            isStreaming={isStreaming}
            agentName={agentName}
            hasKB={hasKB}
            sessions={sessions}
            currentSessionId={currentSessionId}
            onNewChat={() => createNewSession()}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
            onRetryMessage={handleRetryMessage}
            isSearchEnabled={isSearchEnabled}
            onToggleSearch={() => setIsSearchEnabled(!isSearchEnabled)}
            isKBEnabled={isKBEnabled}
            onToggleKB={() => setIsKBEnabled(!isKBEnabled)}
            hasDB={hasDB}
            isDBEnabled={isDBEnabled}
            onToggleDB={() => setIsDBEnabled(!isDBEnabled)}
            hasMCP={hasMCP}
        />
    );
}
