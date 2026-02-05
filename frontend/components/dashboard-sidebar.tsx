"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  BookOpen, 
  LayoutDashboard, 
  LineChart, 
  MessageSquare, 
  Settings, 
  ShieldCheck, 
  Upload, 
  User,
  Brain,
  FileCheck,
  Star,
  TrendingUp,
  Flame
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"

const items = [
  {
    title: "Dashboard",
    url: "/protected",
    icon: LayoutDashboard,
  },
  {
    title: "Subjects",
    url: "/protected/subjects",
    icon: BookOpen,
  },
  {
    title: "Upload",
    url: "/protected/upload",
    icon: Upload,
  },
  {
    title: "Predictions",
    url: "/protected/predictions",
    icon: LineChart,
  },
  {
    title: "AI Tutor",
    url: "/protected/chat",
    icon: Brain,
  },
  {
    title: "Mock Tests",
    url: "/protected/tests",
    icon: FileCheck,
  },
  {
    title: "Important Questions",
    url: "/protected/questions",
    icon: Star,
  },
  {
    title: "Trend Analysis",
    url: "/protected/analysis",
    icon: TrendingUp,
  },
]

export function DashboardSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-16 flex items-center px-6">
        <div className="flex items-center gap-2 font-bold text-xl text-primary">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-primary-foreground">
            P
          </div>
          <span className="group-data-[collapsible=icon]:hidden">PrepIQ</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton
                asChild
                isActive={pathname === item.url}
                tooltip={item.title}
                className="hover:bg-primary/10 hover:text-primary transition-colors"
              >
                <Link href={item.url}>
                  <item.icon className="h-4 w-4" />
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter className="p-4 border-t">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Profile">
              <Link href="/protected/profile">
                <User className="h-4 w-4" />
                <span>My Profile</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Settings">
              <Link href="/protected/settings">
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton tooltip="Streak">
              <Flame className="h-4 w-4 text-orange-500" />
              <span>Streak: 0 days</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}