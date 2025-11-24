"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

export const title = "Edit User Profile";

export default function CrudEditUser01() {
  return (
    <section className="container mx-auto py-16 max-w-2xl">
      <Card className="w-full p-6 lg:p-8">
        <div className="mb-6">
          <h3 className="text-2xl font-semibold">Edit Profile</h3>
          <p className="text-muted-foreground mt-1 text-sm">
            Manage user profile information, role assignments, and account
            status.
          </p>
        </div>
        <form action="#" className="space-y-6">
          <div className="flex flex-col items-center gap-4 sm:flex-row">
            <div className="bg-primary/10 flex h-24 w-24 items-center justify-center rounded-full text-3xl font-semibold">
              JD
            </div>
            <div className="text-center sm:text-left">
              <Button variant="outline" size="sm">
                Change Picture
              </Button>
              <p className="text-muted-foreground mt-2 text-xs">
                JPG, GIF or PNG. Max size of 800K
              </p>
            </div>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                name="firstName"
                type="text"
                placeholder="e.g. John"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                name="lastName"
                type="text"
                placeholder="e.g. Doe"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="e.g. john.doe@example.com"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="bio">Bio</Label>
            <Textarea
              id="bio"
              name="bio"
              placeholder="Tell us about yourself..."
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">Role</Label>
            <Select name="role">
              <SelectTrigger id="role" className="w-full">
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="manager">Manager</SelectItem>
                <SelectItem value="user">User</SelectItem>
                <SelectItem value="guest">Guest</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="status">Account Status</Label>
              <p className="text-muted-foreground text-sm">
                Enable or disable this user account
              </p>
            </div>
            <Switch id="status" />
          </div>

          <div className="flex gap-4">
            <Button type="submit" className="flex-1">
              Save Changes
            </Button>
            <Button type="button" variant="destructive" className="flex-1">
              Delete User
            </Button>
          </div>
        </form>
      </Card>
    </section>
  );
}
