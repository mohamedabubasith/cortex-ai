"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import ChatInterface, { ChatSession } from "@/components/ChatInterface";
import api from "@/lib/api";
import config from "@/lib/config";

interface Message {
    role: "user" | "assistant";
    content: string;
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
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string>("");
    const [loading, setLoading] = useState(true);
    // Removed isFirstVisit flag for persistent session handling

    useEffect(() => {
        const initChat = async () => {
            if (params.shareId) {
                // Check if user was on a specific session (from localStorage)
                const savedSessionId = localStorage.getItem(`currentSession_${params.shareId}`);

                // IMPORTANT: Fetch agent info FIRST to get first_message
                await fetchAgentInfo();

                // Then load sessions (will use first_message if needed)
                await loadSessions(savedSessionId || undefined);
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
                return data.first_message || "";
            }
        } catch (error) {
            console.error("Failed to fetch agent info", error);
        }
        return "";
    };

    const loadSessions = async (restoredSessionId?: string) => {
        console.log(`[loadSessions] Fetching sessions for agent: ${params.shareId}`);

        // Get current first message from state or fetch it
        let firstMessage = agentFirstMessage;
        if (!firstMessage) {
            const response = await fetch(`${config.apiV1Url}/chat/public/${params.shareId}`);
            if (response.ok) {
                const data = await response.json();
                firstMessage = data.first_message || "";
            }
        }

        try {
            setLoading(true);
            const url = `${config.apiV1Url}/chat/public/${params.shareId}/sessions`;
            console.log(`[loadSessions] Calling: ${url}`);
            const response = await fetch(url);

            if (response.ok) {
                const backendSessions: BackendSession[] = await response.json();

                // Convert backend sessions to frontend format
                const sessionsList: ChatSession[] = backendSessions.map(s => ({
                    id: s.id,
                    title: s.messages.find(m => m.role === "user")?.content.substring(0, 50) || "New chat",
                    timestamp: new Date(s.created_at).getTime()
                }));

                setSessions(sessionsList);

                // If user was on a specific session (refresh), restore it
                if (restoredSessionId && backendSessions.find(s => s.id === restoredSessionId)) {
                    console.log(`[loadSessions] Restoring session: ${restoredSessionId}`);
                    setCurrentSessionId(restoredSessionId);
                    setSessionId(restoredSessionId);
                    await loadSessionMessages(restoredSessionId);
                } else if (backendSessions.length > 0) {
                    // User has sessions but no saved session - load most recent
                    const latest = backendSessions[0];
                    setCurrentSessionId(latest.id);
                    setSessionId(latest.id);
                    await loadSessionMessages(latest.id);
                } else {
                    // First visit or no sessions - show new chat with first message
                    console.log(`[loadSessions] First visit - showing first message: "${firstMessage}"`);
                    setMessages(firstMessage ? [{ role: "assistant", content: firstMessage }] : []);
                    setLoading(false);
                }
            } else if (response.status === 404) {
                // Agent not found
                console.error("Agent not found");
                setLoading(false);
            } else {
                // No sessions yet - show new chat with first message
                console.log(`[loadSessions] No sessions - showing first message: "${firstMessage}"`);
                setMessages(firstMessage ? [{ role: "assistant", content: firstMessage }] : []);
                setLoading(false);
            }
        } catch (error) {
            console.error("Failed to load sessions", error);
            setMessages(firstMessage ? [{ role: "assistant", content: firstMessage }] : []);
            setLoading(false);
        }
    };

    const loadSessionMessages = async (sessionIdToLoad: string) => {
        try {
            const response = await fetch(`${config.apiV1Url}/chat/public/${params.shareId}/sessions/${sessionIdToLoad}/messages`);

            if (response.ok) {
                const backendMessages = await response.json();
                const messagesList: Message[] = backendMessages.map((m: any) => ({
                    role: m.role as "user" | "assistant",
                    content: m.content
                }));
                setMessages(messagesList);
            }
        } catch (error) {
            console.error("Failed to load messages", error);
        } finally {
            setLoading(false);
        }
    };

    const createNewSession = () => {
        setCurrentSessionId("");
        setSessionId(null);
        setMessages(agentFirstMessage ? [{ role: "assistant", content: agentFirstMessage }] : []);
        localStorage.removeItem(`currentSession_${params.shareId}`);
    };

    const handleSelectSession = async (selectedSessionId: string) => {
        setCurrentSessionId(selectedSessionId);
        setSessionId(selectedSessionId);
        localStorage.setItem(`currentSession_${params.shareId}`, selectedSessionId);
        await loadSessionMessages(selectedSessionId);
    };

    const handleDeleteSession = async (sessionIdToDelete: string) => {
        try {
            // Call backend to delete the session
            const response = await fetch(
                `${config.apiV1Url}/chat/public/${params.shareId}/sessions/${sessionIdToDelete}`,
                { method: 'DELETE' }
            );

            if (response.ok) {
                console.log(`[handleDeleteSession] Session ${sessionIdToDelete} deleted successfully`);

                // If we deleted the current session, switch to another one or create new
                if (sessionIdToDelete === currentSessionId) {
                    // Reload all sessions and load the most recent one
                    await loadSessions();
                } else {
                    // Just remove from the list
                    setSessions(prev => prev.filter(s => s.id !== sessionIdToDelete));
                }
            } else {
                console.error("Failed to delete session");
            }
        } catch (error) {
            console.error("Failed to delete session", error);
        }
    };

    const handleSendMessage = async (message: string) => {
        setIsStreaming(true);

        // Add user message optimistically
        const userMessage = { role: "user" as const, content: message };
        // Create placeholder for assistant message immediately to show typing indicator
        setMessages((prev) => [...prev, userMessage, { role: "assistant", content: "" }]);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 min timeout

        try {
            const response = await fetch(`${config.apiV1Url}/chat/public/${params.shareId}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message,
                    session_id: sessionId,
                    model: "default"
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }
            if (!response.body) throw new Error("No response body");

            // Assistant message is already in the list (last item)

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = "";
            let updateScheduled = false;
            let chunkCount = 0;
            const maxChunks = 10000; // Safety limit

            // Function to update UI with batching
            const updateUI = () => {
                setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = { role: "assistant", content: assistantMessage };
                    return updated;
                });
                updateScheduled = false;
            };

            // Read stream with error handling
            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    chunkCount++;

                    // Safety check for very long responses
                    if (chunkCount > maxChunks) {
                        console.warn(`Exceeded max chunks (${maxChunks}), stopping stream`);
                        assistantMessage += "\n\n[Response truncated - maximum length reached]";
                        updateUI();
                        break;
                    }

                    const chunk = decoder.decode(value, { stream: true });
                    assistantMessage += chunk;

                    // Batch updates using requestAnimationFrame to prevent too many re-renders
                    if (!updateScheduled) {
                        updateScheduled = true;
                        requestAnimationFrame(updateUI);
                    }
                }
            } catch (streamError) {
                console.error("Stream reading error:", streamError);
                assistantMessage += "\n\n[Stream interrupted]";
            } finally {
                reader.releaseLock();
            }

            // Final update to ensure we have the complete message
            updateUI();

            // Update session ID if it was created during this chat
            if (!sessionId && response.headers.get('x-session-id')) {
                const newSessionId = response.headers.get('x-session-id');
                setSessionId(newSessionId);
                setCurrentSessionId(newSessionId || '');
                if (newSessionId) {
                    localStorage.setItem(`currentSession_${params.shareId}`, newSessionId);

                    // Add to sessions list immediately
                    setSessions(prev => [
                        {
                            id: newSessionId,
                            title: message.substring(0, 50) || "New chat",
                            timestamp: Date.now()
                        },
                        ...prev
                    ]);
                }
            }

        } catch (error: any) {
            console.error("Failed to send message:", error);

            // Display error message to user
            let errorMsg = "Error: Failed to get response.";
            if (error.name === 'AbortError') {
                errorMsg = "Error: Request timed out. The response took too long.";
            } else if (error.message) {
                errorMsg = `Error: ${error.message}`;
            }

            setMessages((prev) => {
                const updated = [...prev];
                // Replace empty assistant message with error
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
        // Find the user message that preceded this error message
        let userMessageIndex = -1;
        for (let i = messageIndex - 1; i >= 0; i--) {
            if (messages[i].role === "user") {
                userMessageIndex = i;
                break;
            }
        }

        if (userMessageIndex !== -1) {
            const userMessage = messages[userMessageIndex].content;
            console.log(`[handleRetryMessage] Retrying message: "${userMessage}"`);

            // Remove everything from the user message onwards (includes user msg + error)
            // This prevents duplicates since handleSendMessage adds user message optimistically
            setMessages(prev => prev.slice(0, userMessageIndex));

            // Small delay to prevent flicker
            await new Promise(resolve => setTimeout(resolve, 100));

            // Resend the message
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

    return (
        <ChatInterface
            initialMessages={messages}
            onSendMessage={handleSendMessage}
            isStreaming={isStreaming}
            agentName={agentName}
            sessions={sessions}
            currentSessionId={currentSessionId}
            onNewChat={createNewSession}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
            onRetryMessage={handleRetryMessage}
        />
    );
}
