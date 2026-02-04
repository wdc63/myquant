<template>
  <div ref="editorRef" class="editor-container"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue';
import * as monaco from 'monaco-editor';

const props = defineProps({
  modelValue: String,
  language: String,
  theme: {
    type: String,
    default: 'vs-dark',
  },
  readOnly: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue']);

const editorRef = ref(null);
let editor = null;
let resizeObserver = null;

onMounted(() => {
  if (editorRef.value) {
    editor = monaco.editor.create(editorRef.value, {
      value: props.modelValue || '',
      language: props.language,
      theme: props.theme,
      automaticLayout: false, // Disable automatic layout
      minimap: { enabled: !props.readOnly },
      scrollBeyondLastLine: false,
      wordWrap: 'on',
      readOnly: props.readOnly,
      padding: {
        top: 16,
        bottom: 16,
      },
    });

    editor.onDidChangeModelContent(() => {
      const currentValue = editor.getValue();
      if (currentValue !== props.modelValue) {
        emit('update:modelValue', currentValue);
      }
    });

    // Use ResizeObserver to handle layout changes
    resizeObserver = new ResizeObserver(() => {
      if (editor) {
        editor.layout();
      }
    });
    resizeObserver.observe(editorRef.value);
  }
});

watch(() => props.modelValue, (newValue) => {
  if (editor && newValue !== editor.getValue()) {
    editor.setValue(newValue || '');
  }
});

watch(() => props.language, (newLanguage) => {
  if (editor && monaco.editor.getModels().length > 0) {
    monaco.editor.setModelLanguage(editor.getModel(), newLanguage);
  }
});

watch(() => props.theme, (newTheme) => {
  if (editor) {
    monaco.editor.setTheme(newTheme);
  }
});

onBeforeUnmount(() => {
  if (editor) {
    editor.dispose();
  }
  if (resizeObserver && editorRef.value) {
    resizeObserver.unobserve(editorRef.value);
  }
});
</script>

<style scoped>
.editor-container {
  width: 100%;
  height: 100%;
  overflow: hidden; /* Prevent weird scrollbars */
  border-radius: 6px;
}

/* Light theme background */
.editor-container :deep(.monaco-editor.vs) {
  background-color: #f8fafc !important;
}

.editor-container :deep(.monaco-editor.vs .margin) {
  background-color: #f1f5f9 !important;
}

/* Dark theme background - keep default */
.editor-container :deep(.monaco-editor.vs-dark) {
  background-color: #1e1e1e !important;
}

.editor-container :deep(.monaco-editor.vs-dark .margin) {
  background-color: #1e1e1e !important;
}
</style>
