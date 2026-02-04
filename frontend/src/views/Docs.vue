<template>
  <div class="docs-container">
    <!-- 侧边栏导航 -->
    <aside class="docs-aside" :class="{ 'mobile-nav-open': mobileNavOpen }">
      <div class="mobile-nav-toggle" :class="{ 'open': mobileNavOpen }" @click="toggleMobileNav">
        <span>文档导航</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
      <div class="docs-nav-container">
        <nav>
          <h3 class="nav-title" @click="scrollTo('qtrader-framework')">QTrader 策略框架</h3>
          <ul>
            <li><a @click="scrollTo('qtrader-quickstart')" class="nav-link">快速上手</a></li>
            <li><a @click="scrollTo('qtrader-lifecycle')" class="nav-link">生命周期方法</a></li>
            <li><a @click="scrollTo('qtrader-context')" class="nav-link">Context 上下文</a></li>
            <li><a @click="scrollTo('qtrader-config')" class="nav-link">配置文件说明</a></li>
            <li><a @click="scrollTo('qtrader-dataprovider')" class="nav-link">数据提供者</a></li>
          </ul>

          <h3 class="nav-title" @click="scrollTo('data-provider')">数据接口（DataProvider）</h3>
          <ul>
            <li><a @click="scrollTo('data-contract')" class="nav-link">数据合约（3个方法）</a></li>
            <li><a @click="scrollTo('template')" class="nav-link">模板与示例</a></li>
            <li><a @click="scrollTo('wire')" class="nav-link">平台如何接入</a></li>
          </ul>

          <h3 class="nav-title" @click="scrollTo('libraries')">平台库管理</h3>
          <ul>
            <li><a @click="scrollTo('builtin-libs')" class="nav-link">内置库说明</a></li>
            <li><a @click="scrollTo('custom-libs')" class="nav-link">自定义库管理</a></li>
          </ul>
        </nav>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="docs-main" ref="mainContent">
      <div class="search-container">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input
            v-model="searchQuery"
            @input="handleSearch"
            @focus="handleFocus"
            type="text"
            placeholder="搜索文档..."
            class="search-input"
          />
          <button v-if="searchQuery" @click="clearSearch" class="clear-btn">×</button>
        </div>
        <div v-if="showResults && searchResults.length > 0" class="search-results">
          <div
            v-for="(result, index) in searchResults"
            :key="index"
            @click="jumpToResult(result)"
            class="search-result-item"
          >
            <div class="result-title">{{ result.title }}</div>
            <div class="result-context" v-html="result.context"></div>
          </div>
        </div>
        <div v-if="showResults && searchQuery && searchResults.length === 0" class="search-no-results">
          未找到相关内容
        </div>
      </div>
      <div class="doc-content" v-html="renderedContent"></div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue';
import { marked } from 'marked';
import hljs from 'highlight.js';

const mainContent = ref(null);
const searchQuery = ref('');
const searchResults = ref([]);
const showResults = ref(false);
const searchIndex = ref([]);
const renderedContent = ref('');
const mobileNavOpen = ref(true); // 移动端默认展开导航栏

// THEME - 监听全局主题切换
const isDark = ref(document.body.classList.contains('dark-mode'));
const themeObserver = new MutationObserver(() => {
  isDark.value = document.body.classList.contains('dark-mode');
  updateHighlightTheme();

  // 主题切换后重新应用代码高亮
  nextTick(() => {
    const codeBlocks = mainContent.value?.querySelectorAll('pre code');
    if (codeBlocks) {
      codeBlocks.forEach(block => {
        // 移除旧的高亮类
        block.removeAttribute('data-highlighted');
        hljs.highlightElement(block);
      });
      console.log('主题切换后重新应用代码高亮');
    }
  });
});

// 动态加载 highlight.js 主题
const updateHighlightTheme = () => {
  console.log('切换主题:', isDark.value ? '深色' : '浅色');

  // 移除现有的 highlight.js 样式
  const existingLinks = document.querySelectorAll('link[data-hljs-theme]');
  console.log('移除旧样式数量:', existingLinks.length);
  existingLinks.forEach(link => link.remove());

  // 创建新的样式链接
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.setAttribute('data-hljs-theme', 'true');

  if (isDark.value) {
    link.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css';
  } else {
    link.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';
  }

  console.log('加载样式:', link.href);

  link.onload = () => {
    console.log('highlight.js 样式加载成功');
  };

  link.onerror = (err) => {
    console.error('highlight.js 样式加载失败:', err);
  };

  document.head.appendChild(link);
};

// 文档内容将从外部文件加载


const toggleMobileNav = () => {
  mobileNavOpen.value = !mobileNavOpen.value;
};

const scrollTo = (id) => {
  // 在移动端，点击导航项后自动关闭导航栏
  if (window.innerWidth <= 768) {
    mobileNavOpen.value = false;
  }

  nextTick(() => {
    if (mainContent.value) {
      const element = mainContent.value.querySelector(`#${id}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  });
};

// 构建搜索索引
const buildSearchIndex = () => {
  const index = [];

  // 直接从实际渲染的DOM中提取内容
  if (!mainContent.value) {
    console.warn('mainContent not ready, retrying...');
    setTimeout(buildSearchIndex, 100);
    return;
  }

  const docContent = mainContent.value.querySelector('.doc-content');
  if (!docContent) {
    console.warn('doc-content not found, retrying...');
    setTimeout(buildSearchIndex, 100);
    return;
  }

  // 获取所有标题和内容段落
  const headers = docContent.querySelectorAll('h1, h2, h3, h4');

  headers.forEach(header => {
    const id = header.id;
    const title = header.textContent.trim();

    // 获取该标题下的所有内容，直到下一个同级或更高级标题
    let content = '';
    let currentElement = header.nextElementSibling;

    while (currentElement) {
      const tagName = currentElement.tagName;

      // 如果遇到同级或更高级标题，停止
      if (tagName === 'H1' || tagName === 'H2' || tagName === 'H3' || tagName === 'H4') {
        const currentLevel = parseInt(header.tagName.substring(1));
        const nextLevel = parseInt(tagName.substring(1));
        if (nextLevel <= currentLevel) break;
      }

      // 提取文本内容
      const text = currentElement.textContent.trim();
      if (text) {
        content += text + ' ';
      }

      currentElement = currentElement.nextElementSibling;
    }

    // 添加到索引
    if (id && title) {
      index.push({
        id,
        title,
        content: content.substring(0, 1000) // 增加内容长度以提高搜索准确性
      });
    }
  });

  searchIndex.value = index;
  console.log(`搜索索引构建完成，共 ${index.length} 个条目`);
};

// 处理聚焦事件
const handleFocus = () => {
  showResults.value = true;
  // 如果有搜索内容，重新触发搜索（以防之前被关闭了）
  if (searchQuery.value.trim()) {
    handleSearch();
  }
};

// 在正文中高亮搜索词
const highlightInContent = (query) => {
  if (!mainContent.value) return;

  const docContent = mainContent.value.querySelector('.doc-content');
  if (!docContent) return;

  // 先移除之前的高亮
  removeHighlightInContent();

  if (!query) return;

  // 转义特殊字符
  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escapedQuery})`, 'gi');

  // 递归遍历所有文本节点并高亮
  const highlightTextNodes = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent;
      if (regex.test(text)) {
        // 创建一个临时容器
        const span = document.createElement('span');
        span.innerHTML = text.replace(regex, '<mark class="search-highlight">$1</mark>');

        // 替换原始文本节点
        const fragment = document.createDocumentFragment();
        while (span.firstChild) {
          fragment.appendChild(span.firstChild);
        }
        node.parentNode.replaceChild(fragment, node);
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      // 跳过脚本和样式标签，但保留代码块以便高亮
      if (['SCRIPT', 'STYLE'].includes(node.tagName)) {
        return;
      }
      // 递归处理子节点
      Array.from(node.childNodes).forEach(highlightTextNodes);
    }
  };

  highlightTextNodes(docContent);
};

// 移除正文中的高亮
const removeHighlightInContent = () => {
  if (!mainContent.value) return;

  const docContent = mainContent.value.querySelector('.doc-content');
  if (!docContent) return;

  // 找到所有高亮的mark标签
  const highlights = docContent.querySelectorAll('mark.search-highlight');
  highlights.forEach(mark => {
    const parent = mark.parentNode;
    // 用文本内容替换mark标签
    parent.replaceChild(document.createTextNode(mark.textContent), mark);
    // 合并相邻的文本节点
    parent.normalize();
  });
};

// 搜索处理
const handleSearch = () => {
  const query = searchQuery.value.trim();

  if (!query) {
    searchResults.value = [];
    showResults.value = false;
    removeHighlightInContent();
    return;
  }

  // 如果索引还没构建好，等待
  if (searchIndex.value.length === 0) {
    console.warn('搜索索引尚未构建完成');
    return;
  }

  const results = [];
  const queryLower = query.toLowerCase();

  searchIndex.value.forEach(item => {
    const titleLower = item.title.toLowerCase();
    const contentLower = item.content.toLowerCase();

    // 多种匹配策略
    let matchScore = 0;
    let matchType = '';

    // 1. 完整匹配 (权重最高)
    if (titleLower.includes(queryLower) || contentLower.includes(queryLower)) {
      matchScore += 100;
      matchType = titleLower.includes(queryLower) ? 'title_full' : 'content_full';
    }

    // 2. 拆分字符匹配 (支持中文部分匹配)
    // 只有在查询词长度>=2且没有完整匹配时才启用
    let charMatches = 0;
    if (queryLower.length >= 2 && matchScore === 0) {
      const queryChars = queryLower.split('');
      let matchedChars = 0;

      queryChars.forEach(char => {
        // 计算该字符在标题和内容中的出现次数
        const titleCount = (titleLower.match(new RegExp(char, 'g')) || []).length;
        const contentCount = (contentLower.match(new RegExp(char, 'g')) || []).length;

        if (titleCount > 0) {
          charMatches += 2 * Math.min(titleCount, 3); // 标题中最多计算3次
          matchedChars++;
        }
        if (contentCount > 0) {
          charMatches += Math.min(contentCount, 2); // 内容中最多计算2次
          if (titleCount === 0) matchedChars++;
        }
      });

      // 只有当匹配的字符数 >= 查询词字符数的60%时才计入
      if (matchedChars >= Math.ceil(queryChars.length * 0.6)) {
        matchScore = charMatches;
        matchType = 'partial';
      }
    }

    // 3. 英文单词边界匹配
    const words = queryLower.split(/\s+/);
    let wordMatches = 0;
    words.forEach(word => {
      if (word.length > 1) {
        const wordRegex = new RegExp(`\\b${word}`, 'i');
        if (wordRegex.test(titleLower)) wordMatches += 3;
        if (wordRegex.test(contentLower)) wordMatches += 2;
      }
    });

    if (wordMatches > 0) {
      matchScore += wordMatches * 10;
      matchType = matchType ? `${matchType}_word` : 'word';
    }

    // 如果有任何匹配，添加到结果
    if (matchScore > 0) {
      // 提取匹配上下文
      let context = '';
      let contextIndex = -1;
      let matchedTerm = query; // 默认显示完整查询词

      // 优先查找完整匹配的位置
      if (contentLower.includes(queryLower)) {
        contextIndex = contentLower.indexOf(queryLower);
      } else if (matchType.includes('partial') || matchType.includes('word')) {
        // 对于部分匹配，查找最相关的匹配位置
        const queryChars = queryLower.split('');
        let bestIndex = -1;
        let bestScore = 0;

        queryChars.forEach(char => {
          const index = contentLower.indexOf(char);
          if (index !== -1) {
            // 计算该位置周围匹配字符的数量
            const start = Math.max(0, index - 5);
            const end = Math.min(contentLower.length, index + queryLower.length + 5);
            const contextSegment = contentLower.substring(start, end);

            let score = 0;
            queryChars.forEach(c => {
              if (contextSegment.includes(c)) score++;
            });

            if (score > bestScore || (score === bestScore && index < bestIndex)) {
              bestScore = score;
              bestIndex = index;
            }
          }
        });

        if (bestIndex !== -1) {
          contextIndex = bestIndex;
          // 找到实际匹配的字符作为显示词
          matchedTerm = contentLower.substring(bestIndex, Math.min(bestIndex + 1, contentLower.length));
        }
      }

      if (contextIndex !== -1) {
        // 从匹配位置前50字符开始，提取150字符
        const start = Math.max(0, contextIndex - 50);
        const end = Math.min(item.content.length, contextIndex + matchedTerm.length + 100);
        context = item.content.substring(start, end);

        // 如果不是从开头开始，添加省略号
        if (start > 0) context = '...' + context;
        if (end < item.content.length) context = context + '...';

        // 高亮匹配的关键词（转义特殊字符）
        const escapedTerm = matchedTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedTerm})`, 'gi');
        context = context.replace(regex, '<mark>$1</mark>');
      } else if (titleLower.includes(queryLower)) {
        // 如果只在标题中匹配，显示内容摘要
        context = item.content.substring(0, 150);
        if (item.content.length > 150) context += '...';
      } else {
        // 显示内容摘要
        context = item.content.substring(0, 150);
        if (item.content.length > 150) context += '...';
      }

      results.push({
        id: item.id,
        title: item.title,
        context: context,
        score: matchScore,
        matchType: matchType
      });
    }
  });

  // 按匹配分数排序
  results.sort((a, b) => b.score - a.score);

  searchResults.value = results.slice(0, 10); // 最多显示10个结果
  showResults.value = true;

  // 在正文中高亮搜索词
  highlightInContent(query);

  console.log(`搜索 "${query}" 找到 ${results.length} 个结果 (共检查了 ${searchIndex.value.length} 个索引项)`);
  console.log('匹配类型分布:', results.reduce((acc, r) => {
    acc[r.matchType] = (acc[r.matchType] || 0) + 1;
    return acc;
  }, {}));

  // 调试：如果结果很少，打印更多信息
  if (results.length < 3 && searchIndex.value.length > 10) {
    console.log('前10个索引项标题:', searchIndex.value.slice(0, 10).map(item => item.title));
    console.log('搜索关键词:', query);
    console.log('查询字符拆分:', queryLower.split(''));
  }
};

// 跳转到搜索结果
const jumpToResult = (result) => {
  showResults.value = false;

  nextTick(() => {
    if (mainContent.value) {
      const element = mainContent.value.querySelector(`#${result.id}`);
      if (element) {
        // 滚动到目标位置
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // 查找该标题之后的第一个搜索高亮（在该章节内）
        setTimeout(() => {
          // 获取该标题元素
          let currentEl = element;
          let foundHighlight = null;

          // 向下查找同级和子级元素，直到遇到下一个同级或更高级标题
          while (currentEl) {
            // 检查当前元素及其子元素中是否有高亮
            const highlight = currentEl.querySelector ? currentEl.querySelector('mark.search-highlight') : null;
            if (highlight) {
              foundHighlight = highlight;
              break;
            }

            // 移动到下一个兄弟节点
            currentEl = currentEl.nextElementSibling;

            // 如果遇到同级或更高级标题，停止
            if (currentEl && ['H1', 'H2', 'H3', 'H4'].includes(currentEl.tagName)) {
              const currentLevel = parseInt(element.tagName.substring(1));
              const nextLevel = parseInt(currentEl.tagName.substring(1));
              if (nextLevel <= currentLevel) break;
            }
          }

          if (foundHighlight) {
            // 滚动到该章节的第一个高亮位置
            foundHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // 给高亮添加闪烁效果
            foundHighlight.style.animation = 'highlight-flash 1s ease-in-out 2';
          } else {
            // 如果该章节没有高亮，就高亮标题
            element.style.backgroundColor = 'rgba(234, 179, 8, 0.15)';
            element.style.transition = 'background-color 0.3s';

            // 2秒后移除高亮
            setTimeout(() => {
              element.style.backgroundColor = '';
            }, 2000);
          }
        }, 500); // 等待滚动完成
      }
    }
  });
};

const clearSearch = () => {
  searchQuery.value = '';
  searchResults.value = [];
  showResults.value = false;
  removeHighlightInContent();
};

// 点击外部关闭搜索结果
const handleClickOutside = (event) => {
  const searchContainer = document.querySelector('.search-container');
  if (searchContainer && !searchContainer.contains(event.target)) {
    showResults.value = false;
  }
};

onMounted(async () => {
  // 初始化主题观察器
  themeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });

  // 加载初始主题样式
  updateHighlightTheme();

  marked.setOptions({
    highlight: function(code, lang) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, { language }).value;
    }
  });

  const docFiles = [
    '/docs/01_qtrader_framework.md',
    '/docs/02_data_provider.md',
  ];

  try {
    const responses = await Promise.all(docFiles.map(file => fetch(file)));

    for (const response of responses) {
      if (!response.ok) {
        throw new Error(`Failed to load documentation file: ${response.url}`);
      }
    }

    const markdownContents = await Promise.all(responses.map(res => res.text()));
    const combinedContent = markdownContents.join('\n');

    renderedContent.value = marked(combinedContent);

    // 等待DOM更新后构建搜索索引和手动高亮代码
    nextTick(() => {
      // 手动对所有代码块应用高亮
      const codeBlocks = mainContent.value?.querySelectorAll('pre code');
      console.log('找到代码块数量:', codeBlocks?.length);
      if (codeBlocks) {
        codeBlocks.forEach(block => {
          hljs.highlightElement(block);
        });
        console.log('代码高亮已应用');
      }
      buildSearchIndex();
    });
  } catch (error) {
    console.error('Error loading or rendering documentation:', error);
    renderedContent.value = '<h1>无法加载文档</h1><p>请检查网络连接或联系管理员。</p>';
  }

  document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  themeObserver.disconnect();
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.docs-container {
  display: flex;
  height: calc(100vh - 100px);
  background-color: var(--card-bg);
  border-radius: 8px;
  overflow: hidden;
}

.docs-aside {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.docs-nav-container {
  padding: 24px;
}

.mobile-nav-toggle {
  display: none; /* 默认隐藏，仅在移动端显示 */
}

.nav-title {
  font-size: 16px;
  font-weight: 600;
  margin-top: 20px;
  margin-bottom: 12px;
  color: var(--text-primary);
  cursor: pointer;
  transition: color 0.2s;
}

.nav-title:hover {
  color: var(--tab-active-color);
}

.nav-title:first-child {
  margin-top: 0;
}

.docs-aside ul {
  list-style: none;
  padding-left: 10px;
}

.docs-aside li {
  margin-bottom: 8px;
}

.nav-link {
  text-decoration: none;
  color: var(--tab-inactive-color);
  font-size: 14px;
  transition: color 0.2s;
  cursor: pointer;
  display: block;
}

.nav-link:hover {
  color: var(--tab-active-color);
  font-weight: 500;
}

.docs-main {
  flex-grow: 1;
  overflow-y: auto;
  padding: 32px 48px;
  position: relative;
}

.search-container {
  position: fixed;
  top: 90px;
  right: 55px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.search-box {
  position: relative;
  width: 250px;
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  display: flex;
  align-items: center;
  padding: 6px 10px;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.search-box:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-icon {
  flex-shrink: 0;
  color: var(--header-info-color);
  margin-right: 6px;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  padding: 0;
}

.search-input::placeholder {
  color: var(--header-info-color);
}

.clear-btn {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: none;
  background: var(--table-hover-bg);
  color: var(--text-primary);
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.clear-btn:hover {
  background: var(--border-color);
}

.search-results {
  position: absolute;
  top: 40px;
  right: 0;
  width: 250px;
  max-height: 450px;
  overflow-y: auto;
  background-color: var(--card-bg);
  opacity: 0.8;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.search-result-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background-color: var(--table-hover-bg);
}

.result-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-context {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
}


.search-no-results {
  position: absolute;
  top: 40px;
  right: 0;
  width: 220px;
  padding: 12px;
  text-align: center;
  background-color: var(--card-bg);
  opacity: 0.98;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--header-info-color);
  font-size: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.search-results::-webkit-scrollbar {
  width: 8px;
}

.search-results::-webkit-scrollbar-track {
  background: var(--table-header-bg);
}

.search-results::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: var(--header-info-color);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .docs-container {
    flex-direction: column;
  }

  .docs-aside {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    position: relative;
    display: flex;
    flex-direction: column;
  }

  .mobile-nav-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    background-color: var(--table-header-bg);
    cursor: pointer;
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .docs-nav-container {
    max-height: 35vh; /* 默认展开，占更小空间 */
    overflow-y: auto;
    transition: max-height 0.3s ease-out;
    padding: 16px;
  }

  .docs-aside:not(.mobile-nav-open) .docs-nav-container {
    max-height: 0; /* 关闭时折叠 */
    overflow: hidden;
    padding: 0; /* 收起时移除padding */
  }

  .mobile-nav-toggle span {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .mobile-nav-toggle svg {
    width: 20px;
    height: 20px;
    color: var(--text-primary);
    transition: transform 0.3s;
  }

  .mobile-nav-toggle.open svg {
    transform: rotate(180deg);
  }

  .docs-main {
    padding: 16px;
    height: auto;
  }

  .search-container {
    position: static;
    margin-bottom: 16px;
    align-items: stretch;
  }

  .search-box {
    width: 100%;
  }

  .search-results,
  .search-no-results {
    position: static;
    width: 100%;
    margin-top: 8px;
  }

  .nav-title {
    font-size: 15px;
    margin-top: 16px;
    margin-bottom: 10px;
  }

  .nav-link {
    font-size: 13px;
  }

  .doc-content {
    max-width: 100%;
  }

  :deep(.doc-content h1) {
    font-size: 1.8em;
  }

  :deep(.doc-content h2) {
    font-size: 1.5em;
    margin-top: 2em;
  }

  :deep(.doc-content h3) {
    font-size: 1.3em;
    margin-top: 1.5em;
  }

  :deep(.doc-content h4) {
    font-size: 1.1em;
  }

  :deep(.doc-content p),
  :deep(.doc-content ul),
  :deep(.doc-content ol) {
    font-size: 14px;
  }

  :deep(.doc-content code) {
    font-size: 12px;
  }

  :deep(.doc-content pre) {
    padding: 0.8em;
    font-size: 12px;
    max-height: 400px;
    overflow-x: auto;
  }

  :deep(.doc-content table) {
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    font-size: 12px;
  }
}

/* 小屏幕进一步优化 */
@media (max-width: 480px) {
  .docs-main {
    padding: 12px;
  }

  .docs-nav-container {
    padding: 12px;
  }

  .nav-title {
    font-size: 14px;
  }

  .nav-link {
    font-size: 12px;
  }

  :deep(.doc-content h1) {
    font-size: 1.6em;
  }

  :deep(.doc-content h2) {
    font-size: 1.4em;
  }

  :deep(.doc-content h3) {
    font-size: 1.2em;
  }

  :deep(.doc-content p),
  :deep(.doc-content ul),
  :deep(.doc-content ol) {
    font-size: 13px;
  }

  :deep(.doc-content code) {
    font-size: 11px;
  }

  :deep(.doc-content pre) {
    font-size: 11px;
    padding: 0.6em;
  }
}

:deep(.doc-content h1),
:deep(.doc-content h2),
:deep(.doc-content h3) {
  color: var(--text-primary);
  font-weight: 600;
  scroll-margin-top: 20px;
}

:deep(.doc-content h1) {
  font-size: 2.2em;
  margin-bottom: 1em;
  padding-bottom: 0.5em;
  border-bottom: 1px solid var(--border-color);
}

:deep(.doc-content h2) {
  font-size: 1.8em;
  margin-top: 2.5em;
  margin-bottom: 1em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--border-color);
}

:deep(.doc-content h3) {
  font-size: 1.4em;
  margin-top: 2em;
  margin-bottom: 0.8em;
}

:deep(.doc-content h4) {
  font-size: 1.2em;
  margin-top: 1.5em;
  margin-bottom: 0.6em;
  color: var(--text-primary);
}

:deep(.doc-content p) {
  line-height: 1.8;
  margin-bottom: 1em;
  color: var(--text-primary);
}

:deep(.doc-content ul),
:deep(.doc-content ol) {
  line-height: 1.8;
  margin-bottom: 1em;
  padding-left: 2em;
}

:deep(.doc-content li) {
  margin-bottom: 0.5em;
}

:deep(.doc-content pre) {
  background-color: var(--table-header-bg);
  padding: 1.2em;
  border-radius: 8px;
  overflow: auto;
  line-height: 1.5;
  margin: 1.5em 0;
  max-height: 600px;
}

:deep(.doc-content pre)::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

:deep(.doc-content pre)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

:deep(.doc-content pre)::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

:deep(.doc-content pre)::-webkit-scrollbar-thumb:hover {
  background: #555;
}

:deep(.doc-content code) {
  font-family: 'Consolas', 'Courier New', monospace;
  background-color: var(--table-hover-bg);
  padding: .2em .4em;
  border-radius: 4px;
  font-size: 0.9em;
}

:deep(.doc-content pre code) {
  background-color: transparent;
  padding: 0;
}

:deep(.doc-content blockquote) {
  border-left: 4px solid var(--border-color);
  padding-left: 1em;
  margin: 1em 0;
  color: var(--tab-inactive-color);
}

:deep(.doc-content strong) {
  font-weight: 600;
  color: var(--text-primary);
}

:deep(.doc-content hr) {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 2em 0;
}

/* 正文搜索高亮样式 - 浅色模式 */
:deep(.doc-content mark.search-highlight) {
  background-color: rgba(234, 179, 8, 0.35);
  padding: 2px 4px;
  border-radius: 3px;
}

/* 正文搜索高亮样式 - 深色模式 */
body.dark-mode :deep(.doc-content mark.search-highlight) {
  background-color: rgba(251, 191, 36, 0.5);
  padding: 2px 4px;
  border-radius: 3px;
}

</style>

<style>
/* 全局样式 - 搜索结果高亮(非scoped,确保v-html渲染的mark标签生效) */
.search-results .result-context mark {
  background-color: rgba(234, 179, 8, 0.35) !important;
  color: #000 !important;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
}

/* 深色模式下搜索结果高亮 */
body.dark-mode .search-results .result-context mark {
  background-color: rgba(251, 191, 36, 0.5) !important;
  color: #2d3748 !important;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
}

/* 移动端高亮闪烁动画 */
@keyframes highlight-flash {
  0%, 100% {
    background-color: transparent;
  }
  50% {
    background-color: rgba(234, 179, 8, 0.4);
  }
}
</style>
