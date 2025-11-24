import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Square, Copy, RotateCcw, ThumbsUp, ThumbsDown, Paperclip, Mic } from "lucide-react";

import { ContentLayout } from "@/components/admin-panel/content-layout";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

import { Conversation } from "@/components/ui/shadcn-io/ai/conversation";
import { Message, MessageContent } from "@/components/ui/shadcn-io/ai/message";
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputTools,
  PromptInputButton,
  PromptInputSubmit
} from "@/components/ui/shadcn-io/ai/prompt-input";
import { Reasoning, ReasoningTrigger, ReasoningContent } from "@/components/ui/shadcn-io/ai/reasoning";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useModelSettings } from "@/store/model-settings";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoning?: string;
  isLoading?: boolean;
}

const AiChatPage = () => {
  const { model: settingsModel, setModel: setSettingsModel } = useModelSettings();
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Use local state for the selector, initialized from settings
  const [selectedModel, setSelectedModel] = useState(settingsModel || "gpt-4o");

  // Sync with settings if they change
  useEffect(() => {
    if (settingsModel) {
      setSelectedModel(settingsModel);
    }
  }, [settingsModel]);

  const handleSubmit = async (messageText?: string) => {
    const textToSend = messageText || input.trim();
    if (!textToSend || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
    };

    // 只有在没有提供 messageText 时才添加用户消息（避免重新生成时重复）
    if (!messageText) {
      setMessages((prev) => [...prev, userMessage]);
      setInput("");
    }
    setIsLoading(true);

    try {
      // Get current LLM config from settings
      let { provider, model, apiKey, baseUrl } = useModelSettings.getState();

      // 智能 provider 转换：custom -> openai（OpenAI 兼容格式）
      if (provider === "custom" && baseUrl) {
        console.log("🔄 检测到 custom provider，自动转换为 openai 兼容格式");
        provider = "openai";

        // 移除末尾的 /v1（如果有），LiteLLM 会自动添加正确的端点路径
        baseUrl = baseUrl.replace(/\/v1\/?$/, "").replace(/\/+$/, "");

        // 移除 custom/ 前缀（如果有）
        model = model.replace(/^custom\//, "");

        console.log(`✅ 配置已转换: provider=${provider}, baseUrl=${baseUrl}, model=${model}`);
      }

      // Call real backend API with LLM config
      const response = await fetch("http://localhost:8080/api/llm/player", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          type: "conversation_request",
          playerName: "User",
          companionName: "AI",
          message: textToSend,
          timestamp: new Date().toISOString(),
          llmConfig: {
            provider,
            model,
            apiKey,
            baseUrl,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.message || data.content || "No response from AI",
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("API call failed:", error);

      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `错误: ${error instanceof Error ? error.message : "Failed to get AI response"}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async (messageId: string) => {
    // 找到当前 AI 消息的索引
    const messageIndex = messages.findIndex((msg) => msg.id === messageId);
    if (messageIndex === -1) return;

    // 找到上一条用户消息
    let userMessage: ChatMessage | undefined;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        userMessage = messages[i];
        break;
      }
    }

    if (!userMessage) {
      console.error("无法找到对应的用户消息");
      return;
    }

    // 删除当前 AI 消息
    setMessages((prev) => prev.filter((msg) => msg.id !== messageId));

    // 重新发送请求
    await handleSubmit(userMessage.content);
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content).then(
      () => {
        console.log("内容已复制到剪贴板");
      },
      (err) => {
        console.error("复制失败:", err);
      }
    );
  };

  const handleModelChange = (value: string) => {
    setSelectedModel(value);
    setSettingsModel(value);
  };

  return (
    <ContentLayout title="AI 对话测试">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/">主页</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>AI 对话测试</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex flex-col h-[calc(100vh-180px)] mt-4">
        <Conversation className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((message) => (
            <Message key={message.id} from={message.role} className="max-w-3xl mx-auto">
              <div className={message.role === "user" ? "ml-auto w-fit space-y-2" : "flex-1 space-y-2"}>
                {message.reasoning && (
                  <Reasoning>
                    <ReasoningTrigger>已思考</ReasoningTrigger>
                    <ReasoningContent>{message.reasoning}</ReasoningContent>
                  </Reasoning>
                )}
                <MessageContent>
                  {message.content}
                </MessageContent>
                {message.role === "assistant" && !message.isLoading && (
                  <div className="flex items-center gap-2 pt-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => handleCopy(message.content)}
                      title="复制"
                    >
                      <Copy className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => handleRegenerate(message.id)}
                      disabled={isLoading}
                      title="重新生成"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                    </Button>
                    <div className="flex-1" />
                    <Button variant="ghost" size="icon" className="h-6 w-6" title="点赞">
                      <ThumbsUp className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-6 w-6" title="点踩">
                      <ThumbsDown className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                )}
              </div>
            </Message>
          ))}
          {isLoading && (
            <Message from="assistant" className="max-w-3xl mx-auto">
              <MessageContent>
                <span className="animate-pulse">Thinking...</span>
              </MessageContent>
            </Message>
          )}
        </Conversation>

        <div className="p-4 bg-background">
          <div className="max-w-3xl mx-auto space-y-4">
            <PromptInput
              onSubmit={(e) => {
                e.preventDefault();
                handleSubmit();
              }}
              className="border rounded-xl shadow-sm bg-background"
            >
              <PromptInputTextarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="min-h-[60px] max-h-[200px]"
              />
              <PromptInputTools className="justify-between p-2 items-center">
                <div className="flex items-center gap-1">
                  <PromptInputButton size="icon" variant="ghost">
                    <Paperclip className="h-4 w-4" />
                  </PromptInputButton>
                  <PromptInputButton size="icon" variant="ghost">
                    <Mic className="h-4 w-4" />
                  </PromptInputButton>
                  <Select value={selectedModel} onValueChange={handleModelChange}>
                    <SelectTrigger className="w-auto h-8 border-none shadow-none bg-transparent hover:bg-accent/50 gap-1 px-2 text-muted-foreground">
                      <SelectValue placeholder="Model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                      <SelectItem value="claude-3-5-sonnet">Claude 3.5 Sonnet</SelectItem>
                      <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
                      {!["gpt-4o", "claude-3-5-sonnet", "gemini-pro"].includes(selectedModel) && (
                        <SelectItem value={selectedModel}>{selectedModel}</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <PromptInputSubmit
                  disabled={!input.trim() || isLoading}
                  status={isLoading ? "streaming" : undefined}
                  className="rounded-full"
                >
                  {isLoading ? <Square className="h-4 w-4 fill-current" /> : null}
                </PromptInputSubmit>
              </PromptInputTools>
            </PromptInput>

            <div className="text-xs text-center text-muted-foreground">
              AI 可能会生成不准确的信息，请核对重要事实。
            </div>
          </div>
        </div>
      </div>
    </ContentLayout>
  );
};

export default AiChatPage;
export { AiChatPage };
