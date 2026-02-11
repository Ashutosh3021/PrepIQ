"use client"

import { useState } from "react"
import { Send, Bot, Sparkles, Paperclip } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

const initialMessages = [
  {
    id: "1",
    role: "assistant",
    content: "Hi! I'm your PrepIQ AI Tutor. I'm here to help you prepare for your exams. How can I assist you today?",
  },
]

export default function ChatPage() {
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState("")

  const handleSend = () => {
    if (!input.trim()) return
    const newMessages = [...messages, { id: Date.now().toString(), role: "user", content: input }]
    setMessages(newMessages)
    setInput("")

    // Simulate AI response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "That's a great question about partial derivatives! Based on your uploaded notes, the most important thing to remember is the chain rule application for multivariable functions...",
        },
      ])
    }, 1000)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Study Tutor</h1>
          <p className="text-muted-foreground">
            Ask questions about your uploaded materials and get instant academic help.
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full">
          <Sparkles className="h-3 w-3" />
          Powered by PrepIQ AI
        </div>
      </div>

      <Card className="flex-1 overflow-hidden flex flex-col">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                <Avatar className="h-8 w-8 shrink-0">
                  {message.role === "assistant" ? (
                    <>
                      <AvatarImage src="/placeholder-bot.png" />
                      <AvatarFallback className="bg-primary text-primary-foreground">
                        <Bot className="h-4 w-4" />
                      </AvatarFallback>
                    </>
                  ) : (
                    <>
                      <AvatarImage src="" />
                      <AvatarFallback>U</AvatarFallback>
                    </>
                  )}
                </Avatar>
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                    message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="p-4 border-t bg-background">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="flex items-center gap-2"
          >
            <Button variant="ghost" size="icon" type="button" className="shrink-0 text-muted-foreground">
              <Paperclip className="h-5 w-5" />
            </Button>
            <Input
              placeholder="Ask anything about your subjects..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1"
            />
            <Button size="icon" type="submit" className="shrink-0" disabled={!input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  )
}
