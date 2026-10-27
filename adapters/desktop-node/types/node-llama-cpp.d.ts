// node-llama-cpp is not installed on the MacBook (the mini's shared eval-runner node_modules has 3.21.1); the runner
// uses it untyped, like exp-06.
declare module "node-llama-cpp" {
  export const getLlama: any;
  export const LlamaChatSession: any;
  export const LlamaCompletion: any;
  export const resolveChatWrapper: any;
}
