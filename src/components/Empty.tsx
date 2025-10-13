import { toast } from "sonner"

// Empty component
export default function Empty() {
  return (
    <div
      className="flex h-full items-center justify-center"
      onClick={() => toast('Coming soon')}
    >
      Empty
    </div>
  )
}
