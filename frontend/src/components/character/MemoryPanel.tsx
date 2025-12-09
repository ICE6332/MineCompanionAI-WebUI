import { useEffect, useState } from "react";
import { Brain, Search, Clock, Tag } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api, MemoryEntry } from "@/lib/api";

const MemoryTypeBadge = ({ type }: { type: MemoryEntry['type'] }) => {
    switch (type) {
        case 'episodic':
            return <Badge variant="default" className="bg-blue-500 hover:bg-blue-600 text-xs">情景</Badge>;
        case 'semantic':
            return <Badge variant="default" className="bg-emerald-500 hover:bg-emerald-600 text-xs">语义</Badge>;
        case 'procedure':
            return <Badge variant="default" className="bg-purple-500 hover:bg-purple-600 text-xs">程序</Badge>;
        default:
            return <Badge variant="secondary" className="text-xs">{type}</Badge>;
    }
};

interface MemoryPanelProps {
    className?: string;
}

export function MemoryPanel({ className }: MemoryPanelProps) {
    const [memories, setMemories] = useState<MemoryEntry[]>([]);
    const [search, setSearch] = useState("");
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadMemories = async () => {
            setIsLoading(true);
            try {
                // 暂时使用模拟的 Session ID
                const data = await api.getMemories("current", search);
                setMemories(data);
            } catch (error) {
                console.error("加载记忆失败", error);
            } finally {
                setIsLoading(false);
            }
        };

        const timer = setTimeout(() => {
            loadMemories();
        }, 300); // 防抖

        return () => clearTimeout(timer);
    }, [search]);

    return (
        <Card className={className}>
            <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                    <Brain className="h-4 w-4" />
                    记忆库
                </CardTitle>
                <div className="relative mt-2">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        type="search"
                        placeholder="搜索记忆..."
                        className="pl-9 h-9"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
            </CardHeader>
            <CardContent className="pt-2">
                <ScrollArea className="h-[300px] pr-4">
                    <div className="space-y-3">
                        {memories.map((memory) => (
                            <div key={memory.id} className="border rounded-lg p-3 space-y-2">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <MemoryTypeBadge type={memory.type} />
                                        <span className="text-xs text-muted-foreground font-mono">
                                            IMP: {memory.importance.toFixed(1)}
                                        </span>
                                    </div>
                                    <div className="flex items-center text-xs text-muted-foreground">
                                        <Clock className="mr-1 h-3 w-3" />
                                        {new Date(memory.timestamp).toLocaleDateString()}
                                    </div>
                                </div>
                                <p className="text-sm leading-relaxed">
                                    {memory.content}
                                </p>
                                {memory.tags && memory.tags.length > 0 && (
                                    <div className="flex flex-wrap gap-1">
                                        {memory.tags.map(tag => (
                                            <Badge key={tag} variant="outline" className="text-xs text-muted-foreground">
                                                <Tag className="mr-1 h-2 w-2" />
                                                {tag}
                                            </Badge>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}

                        {memories.length === 0 && !isLoading && (
                            <div className="text-center py-6 text-muted-foreground text-sm">
                                未找到记忆条目
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
