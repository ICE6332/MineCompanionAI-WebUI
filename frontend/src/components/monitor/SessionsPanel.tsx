import { useEffect, useState } from "react";
import { Plus, Power, RefreshCw, Clock, Activity, Cpu } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { api, EngineSession } from "@/lib/api";

interface SessionsPanelProps {
    className?: string;
}

export function SessionsPanel({ className }: SessionsPanelProps) {
    const [sessions, setSessions] = useState<EngineSession[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateOpen, setIsCreateOpen] = useState(false);

    // 表单状态
    const [newSessionId, setNewSessionId] = useState("");
    const [newCharacterId, setNewCharacterId] = useState("");

    const fetchSessions = async () => {
        setLoading(true);
        try {
            const data = await api.getSessions();
            setSessions(data);
        } catch (error) {
            console.error("获取会话列表失败", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSessions();
    }, []);

    const handleCreate = async () => {
        // 模拟创建逻辑
        const newSession: EngineSession = {
            session_id: newSessionId || `sess-${Date.now()}`,
            character_id: newCharacterId || "default-char",
            status: "active",
            created_at: new Date().toISOString(),
            config: { model: "gpt-4o" } // 默认配置
        };

        // 乐观更新
        setSessions([newSession, ...sessions]);
        setIsCreateOpen(false);
        setNewSessionId("");
        setNewCharacterId("");
    };

    const handleTerminate = (sessionId: string) => {
        // 模拟终止
        setSessions(sessions.map(s =>
            s.session_id === sessionId ? { ...s, status: 'terminated' } : s
        ));
    };

    return (
        <Card className={className}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div>
                    <CardTitle className="text-base flex items-center gap-2">
                        <Cpu className="h-4 w-4" />
                        引擎会话
                    </CardTitle>
                </div>
                <div className="flex gap-2">
                    <Button variant="ghost" size="icon" onClick={fetchSessions}>
                        <RefreshCw className="h-4 w-4" />
                    </Button>
                    <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                        <DialogTrigger asChild>
                            <Button size="sm">
                                <Plus className="mr-1 h-4 w-4" />
                                新建
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>初始化新会话</DialogTitle>
                                <DialogDescription>
                                    启动一个新的游戏引擎实例。
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="session-id" className="text-right">
                                        会话 ID
                                    </Label>
                                    <Input
                                        id="session-id"
                                        value={newSessionId}
                                        onChange={(e) => setNewSessionId(e.target.value)}
                                        placeholder="自动生成"
                                        className="col-span-3"
                                    />
                                </div>
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="char-id" className="text-right">
                                        角色 ID
                                    </Label>
                                    <Input
                                        id="char-id"
                                        value={newCharacterId}
                                        onChange={(e) => setNewCharacterId(e.target.value)}
                                        placeholder="e.g. steve-helper"
                                        className="col-span-3"
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button onClick={handleCreate}>启动会话</Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-2">
                {sessions.length === 0 && !loading && (
                    <div className="text-center py-6 text-muted-foreground text-sm">
                        暂无活跃会话
                    </div>
                )}
                {sessions.map((session) => (
                    <div
                        key={session.session_id}
                        className={`border rounded-lg p-3 space-y-2 ${session.status === 'terminated' ? 'opacity-60' : ''}`}
                    >
                        <div className="flex items-center justify-between">
                            <span className="font-mono text-sm truncate">{session.session_id}</span>
                            <Badge
                                variant={session.status === 'active' ? 'default' : session.status === 'idle' ? 'secondary' : 'destructive'}
                            >
                                {session.status === 'active' ? '活跃' : session.status === 'idle' ? '空闲' : '已终止'}
                            </Badge>
                        </div>
                        <div className="flex items-center text-xs text-muted-foreground gap-4">
                            <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {new Date(session.created_at).toLocaleTimeString()}
                            </span>
                            <span className="flex items-center gap-1">
                                <Activity className="h-3 w-3" />
                                {session.config?.model || 'Unknown'}
                            </span>
                        </div>
                        {session.status !== 'terminated' && (
                            <Button
                                variant="outline"
                                size="sm"
                                className="w-full mt-2"
                                onClick={() => handleTerminate(session.session_id)}
                            >
                                <Power className="mr-2 h-3 w-3" />
                                终止
                            </Button>
                        )}
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}
