
"use client";

import { useEffect, useState } from "react";
import { Permission } from "@/types/rbac";
import { cn } from "@/lib/utils";
import { Check, Lock } from "lucide-react";

interface RoleMatrixProps {
    permissions: Permission[];
    selectedSlugs: string[];
    onChange: (slugs: string[]) => void;
    readOnly?: boolean;
    isSystemRole?: boolean;
}

export default function RoleMatrix({ permissions, selectedSlugs, onChange, readOnly = false, isSystemRole = false }: RoleMatrixProps) {
    // 1. Group by Resource (prefix)
    // Structure: { "KB": { "view": permObj, "create": permObj }, "Agent": { ... } }
    const resources = permissions.reduce((acc, perm) => {
        const [resourceRaw, actionRaw] = perm.slug.split('.');
        const resource = resourceRaw.toUpperCase(); // KB, AGENT, IAM
        const action = actionRaw || "manage"; // Fallback

        if (!acc[resource]) acc[resource] = [];
        acc[resource].push({ ...perm, shortAction: action });
        return acc;
    }, {} as Record<string, (Permission & { shortAction: string })[]>);

    const togglePermission = (slug: string) => {
        if (readOnly) return;
        if (selectedSlugs.includes(slug)) {
            onChange(selectedSlugs.filter(s => s !== slug));
        } else {
            onChange([...selectedSlugs, slug]);
        }
    };

    const toggleResource = (resource: string) => {
        if (readOnly) return;
        const resourcePerms = resources[resource].map(p => p.slug);
        const allSelected = resourcePerms.every(s => selectedSlugs.includes(s));

        if (allSelected) {
            onChange(selectedSlugs.filter(s => !resourcePerms.includes(s)));
        } else {
            const newSlugs = new Set([...selectedSlugs, ...resourcePerms]);
            onChange(Array.from(newSlugs));
        }
    };

    return (
        <div className="space-y-4">
            {Object.entries(resources).map(([resource, perms]) => {
                const isAllSelected = perms.every(p => selectedSlugs.includes(p.slug));

                return (
                    <div key={resource} className="border rounded-xl overflow-hidden bg-white dark:bg-[#0f0f0f] dark:border-white/10 shadow-sm">
                        <div className="bg-gray-50/50 dark:bg-white/5 px-4 py-3 flex items-center justify-between border-b dark:border-white/10">
                            <span className="font-bold text-sm text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                                {resource}
                                {isSystemRole && <Lock className="w-3 h-3 text-gray-400" />}
                            </span>
                            {!readOnly && (
                                <button
                                    onClick={() => toggleResource(resource)}
                                    className="text-xs font-medium text-blue-500 hover:text-blue-400"
                                >
                                    {isAllSelected ? "Unselect All" : "Select All"}
                                </button>
                            )}
                        </div>
                        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {perms.map((perm) => {
                                const isSelected = selectedSlugs.includes(perm.slug);
                                return (
                                    <div
                                        key={perm.slug}
                                        onClick={() => togglePermission(perm.slug)}
                                        className={cn(
                                            "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all select-none relative group",
                                            isSelected
                                                ? "bg-nvidia-green/10 border-nvidia-green/50"
                                                : "bg-transparent border-transparent hover:bg-gray-50 dark:hover:bg-white/5",
                                            readOnly && "cursor-default border-transparent"
                                        )}
                                    >
                                        <div className={cn(
                                            "w-5 h-5 rounded border flex items-center justify-center shrink-0 mt-0.5 transition-colors",
                                            isSelected
                                                ? "bg-nvidia-green border-nvidia-green text-black"
                                                : "border-gray-300 dark:border-gray-600 group-hover:border-gray-400"
                                        )}>
                                            {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                                        </div>
                                        <div>
                                            <div className={cn("font-mono text-xs font-bold mb-0.5", isSelected ? "text-nvidia-green dark:text-nvidia-green" : "text-gray-700 dark:text-gray-300")}>
                                                {perm.shortAction.charAt(0).toUpperCase() + perm.shortAction.slice(1)}
                                            </div>
                                            <div className="text-[11px] text-gray-500 leading-tight">
                                                {perm.description || `Manage ${resource}`}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
