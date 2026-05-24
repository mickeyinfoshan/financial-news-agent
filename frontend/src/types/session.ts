export interface Session {
  session_id: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  preview?: string;
}
