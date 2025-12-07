"use client";

import ChatInterface from "@/components/ChatInterface";
import { useState } from "react";

const SAMPLE_MESSAGES: { role: "user" | "assistant"; content: string }[] = [
    {
        role: "user",
        content: "Can you show me what this UI can do? I want to see tables, code, and markdown."
    },
    {
        role: "assistant",
        content: `Here is a demonstration of the **Cortex AI** premium interface.

### 1. Tables
We can render GitHub Flavored Markdown tables beautifully:

| Model | Context Window | Cost | Performance |
|-------|---------------|------|-------------|
| GPT-4 | 128k | $$$ | High |
| Claude 3 | 200k | $$ | High |
| Llama 3 | 8k | $ | Medium |

### 2. Code Blocks
Syntax highlighting is supported for various languages.

**Python:**
\`\`\`python
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Calculate first 10 numbers
print([calculate_fibonacci(i) for i in range(10)])
\`\`\`

**JSON:**
\`\`\`json
{
  "app": "Cortex AI",
  "version": "1.0.0",
  "features": ["RAG", "Chat", "Agents"],
  "active": true
}
\`\`\`

### 3. Rich Text
You can use *italics*, **bold**, [links](https://nvidia.com), and lists:
*   Feature A
*   Feature B
    *   Sub-feature B.1

> "Intelligence is the ability to adapt to change." - Stephen Hawking
`
    }
];

export default function DemoPage() {
    const [messages, setMessages] = useState(SAMPLE_MESSAGES);
    const [isStreaming, setIsStreaming] = useState(false);

    const handleSendMessage = async (message: string) => {
        setIsStreaming(true);

        // Simulate a response for the demo
        setTimeout(() => {
            setMessages(prev => [
                ...prev,
                { role: "user", content: message },
                { role: "assistant", content: "This is a **simulated response** in the demo environment. \n\nI can continue to show you more features if you like!" }
            ]);
            setIsStreaming(false);
        }, 1000);
    };

    return (
        <ChatInterface
            initialMessages={messages}
            onSendMessage={handleSendMessage}
            isStreaming={isStreaming}
        />
    );
}
