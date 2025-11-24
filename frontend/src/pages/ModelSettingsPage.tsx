import { Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { ContentLayout } from "@/components/admin-panel/content-layout";
import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbLink,
    BreadcrumbList,
    BreadcrumbPage,
    BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Link } from "react-router-dom";
import { useModelSettings } from "@/store/model-settings";

export function ModelSettingsPage() {
    const {
        provider, setProvider,
        model, setModel,
        apiKey, setApiKey,
        baseUrl, setBaseUrl
    } = useModelSettings();

    const handleSave = async () => {
        console.log("Saving settings:", { provider, model, apiKey, baseUrl });
        // Zustand persist middleware handles the saving to localStorage automatically

        try {
            const response = await fetch('/api/llm/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ provider, model, apiKey, baseUrl })
            });

            if (response.ok) {
                console.log("Config saved to server");
                alert("✅ 设置已保存到服务器");
            } else {
                console.log("Failed to save config", response.status, response.statusText);
                alert("❌ 保存失败: " + response.statusText);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            console.log("Network error while saving config", message);
            alert("❌ 网络错误: " + message);
        }
    };

    return (
        <ContentLayout title="模型设置">
            <Breadcrumb>
                <BreadcrumbList>
                    <BreadcrumbItem>
                        <BreadcrumbLink asChild>
                            <Link to="/">主页</Link>
                        </BreadcrumbLink>
                    </BreadcrumbItem>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                        <BreadcrumbPage>模型设置</BreadcrumbPage>
                    </BreadcrumbItem>
                </BreadcrumbList>
            </Breadcrumb>

            <div className="mt-6 space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle>LLM 服务配置</CardTitle>
                        <CardDescription>
                            配置 AI 模型的连接参数。支持 OpenAI、DeepSeek 等兼容服务。
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="provider">服务提供商</Label>
                            <Select value={provider} onValueChange={setProvider}>
                                <SelectTrigger id="provider">
                                    <SelectValue placeholder="选择提供商" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="openai">OpenAI (官方)</SelectItem>
                                    <SelectItem value="deepseek">DeepSeek (深度求索)</SelectItem>
                                    <SelectItem value="moonshot">Moonshot (月之暗面)</SelectItem>
                                    <SelectItem value="ollama">Ollama (本地)</SelectItem>
                                    <SelectItem value="custom">自定义 (OpenAI 兼容)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="base-url">Base URL (API 地址)</Label>
                            <Input
                                id="base-url"
                                placeholder="https://api.openai.com/v1"
                                value={baseUrl}
                                onChange={(e) => setBaseUrl(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">
                                如果使用官方 OpenAI，可留空。第三方服务必填 (例如: https://api.deepseek.com/v1)。
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="api-key">API Key (密钥)</Label>
                            <Input
                                id="api-key"
                                type="password"
                                placeholder="sk-..."
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="model">模型名称</Label>
                            <Input
                                id="model"
                                placeholder="gpt-4, deepseek-chat, etc."
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                            />
                        </div>

                        <div className="pt-4">
                            <Button onClick={handleSave}>
                                <Save className="mr-2 h-4 w-4" />
                                保存设置
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </ContentLayout>
    );
}
