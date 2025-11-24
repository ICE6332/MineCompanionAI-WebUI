import { useState } from "react"
import { Link } from "react-router-dom"

import { ContentLayout } from "@/components/admin-panel/content-layout"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import AvatarUpload from "@/components/character/avatar-upload"

const TestCardPage = () => {
  const [character, setCharacter] = useState({
    name: "AI Companion",
    description: "A helpful AI assistant.",
    personality: "Friendly, helpful, and knowledgeable.",
    systemPrompt: "You are a helpful AI assistant.",
    isActive: true,
  })

  const handleAvatarChange = (file: File) => {
    console.log("Avatar changed:", file)
    // Handle file upload logic here
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Saving character:", character)
    // Handle save logic here
  }

  return (
    <ContentLayout title="角色测试">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/">主页</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>角色测试</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <section className="container mx-auto py-6 max-w-4xl space-y-6">
        <header className="space-y-3">
          <h2 className="text-3xl md:text-4xl font-bold">编辑角色卡</h2>
          <p className="text-muted-foreground">
            自定义 AI 角色的外观、性格和行为模式。
          </p>
        </header>

        <Card className="w-full p-6 lg:p-8">
          <div className="mb-6">
            <h3 className="text-2xl font-semibold">角色信息</h3>
            <p className="text-muted-foreground mt-1 text-sm">
              配置角色的基本信息和核心设定。
            </p>
          </div>

          <form onSubmit={handleSave} className="space-y-8">
            <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
              <div className="flex-shrink-0">
                <AvatarUpload onChange={handleAvatarChange} />
                <p className="text-muted-foreground mt-2 text-xs text-center">
                  点击或拖拽上传
                </p>
              </div>
              <div className="flex-1 space-y-4 w-full">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">角色名称</Label>
                    <Input
                      id="name"
                      value={character.name}
                      onChange={(e) => setCharacter({ ...character, name: e.target.value })}
                      placeholder="例如：Emiya"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="isActive">启用状态</Label>
                    <div className="flex items-center gap-2 h-10">
                      <Switch
                        id="isActive"
                        checked={character.isActive}
                        onCheckedChange={(checked) => setCharacter({ ...character, isActive: checked })}
                      />
                      <span className="text-sm text-muted-foreground">
                        {character.isActive ? "已启用" : "已禁用"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">简短描述</Label>
                  <Input
                    id="description"
                    value={character.description}
                    onChange={(e) => setCharacter({ ...character, description: e.target.value })}
                    placeholder="一句话描述角色的主要特征..."
                  />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="personality">性格设定 (Personality)</Label>
                <Textarea
                  id="personality"
                  value={character.personality}
                  onChange={(e) => setCharacter({ ...character, personality: e.target.value })}
                  placeholder="详细描述角色的性格、说话方式和行为习惯..."
                  rows={4}
                  className="resize-y"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="systemPrompt">系统提示词 (System Prompt)</Label>
                <Textarea
                  id="systemPrompt"
                  value={character.systemPrompt}
                  onChange={(e) => setCharacter({ ...character, systemPrompt: e.target.value })}
                  placeholder="角色的核心指令和规则设定..."
                  rows={6}
                  className="font-mono text-sm resize-y"
                />
              </div>
            </div>

            <div className="flex gap-4 pt-4 border-t">
              <Button type="submit" className="flex-1 sm:flex-none sm:w-32">
                保存更改
              </Button>
              <Button type="button" variant="destructive" className="flex-1 sm:flex-none sm:w-32">
                删除角色
              </Button>
            </div>
          </form>
        </Card>
      </section>
    </ContentLayout>
  )
}

export default TestCardPage
export { TestCardPage }
