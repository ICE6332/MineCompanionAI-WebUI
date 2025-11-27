import { useEffect, useRef, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useWsStore } from "@/stores/wsStore";
import { cn } from "@/lib/utils";

interface GameMessage {
    type?: string;
    event?: string;
    playerName?: string;
    companionName?: string;
    message?: string;
    content?: string;
    timestamp?: string;
    role?: string;
    sender?: string;
    [key: string]: any;
}

export default function GameMessageLog() {
    const { messages } = useWsStore();
    const scrollRef = useRef<HTMLDivElement>(null);
    const [parsedMessages, setParsedMessages] = useState<GameMessage[]>([]);

    useEffect(() => {
        try {
            const parsed = messages.map((msg: string) => {
                if (typeof msg === "string") {
                    try {
                        return JSON.parse(msg);
                    } catch {
                        return { message: msg };
                    }
                }
                return msg;
            });
            setParsedMessages(parsed);
        } catch (error) {
            console.error("Failed to parse messages:", error);
        }
    }, [messages]);

    useEffect(() => {
        const scrollContainer = scrollRef.current?.querySelector('[data-radix-scroll-area-viewport]');
        if (scrollContainer) {
            scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }
    }, [parsedMessages]);

    const getMessageContent = (msg: GameMessage) => {
        if (msg.message) return msg.message;
        if (msg.content) return msg.content;
        return JSON.stringify(msg);
    };

    const getSenderName = (msg: GameMessage) => {
        if (msg.playerName) return msg.playerName;
        if (msg.companionName) return msg.companionName;
        if (msg.sender) return msg.sender;
        if (msg.role === "user") return "User";
        if (msg.role === "assistant") return "AI";
        return "Unknown";
    };

    const getAvatarFallback = (name: string) => {
        return name.substring(0, 2).toUpperCase();
    };

    return (
        <ScrollArea className="h-[400px] pr-4" ref={scrollRef}>
            <div className="space-y-4">
                {parsedMessages.length === 0 && (
                    <div className="text-center text-muted-foreground py-8">
                        暂无对话记录
                    </div>
                )}
                {parsedMessages.map((msg, index) => {
                    const sender = getSenderName(msg);
                    const content = getMessageContent(msg);

                    // Filter out messages with Unknown sender
                    if (sender === "Unknown") {
                        return null;
                    }

                    const isUser = sender === "User" || sender === "Player";

                    return (
                        <div key={index} className="flex items-start gap-4">
                            <Avatar className="h-8 w-8 mt-1">
                                <AvatarImage src={`/avatars/${isUser ? "user" : "bot"}.png`} alt="Avatar" />
                                <AvatarFallback>{getAvatarFallback(sender)}</AvatarFallback>
                            </Avatar>
                            <div className="flex flex-col gap-1 min-w-0 flex-1">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium leading-none">{sender}</span>
                                    <span className="text-xs text-muted-foreground">
                                        {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ""}
                                    </span>
                                </div>
                                <div className="text-sm text-muted-foreground break-words whitespace-pre-wrap bg-muted/50 p-2 rounded-md">
                                    {content}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </ScrollArea>
    );
}
