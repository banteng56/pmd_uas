<template>
  <section id="news">
    <v-container fluid>
      <v-row class="mb-4">
        <v-col cols="12">
          <h2 class="text-center">Latest News</h2>
          <p class="text-center text-grey">
            Page {{ currentPage }} of {{ totalPages }} 
            <span v-if="totalArticles">({{ totalArticles }} articles total)</span>
          </p>
        </v-col>
      </v-row>

      <v-row v-if="loading" class="justify-center">
        <v-col cols="12" class="text-center">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
          ></v-progress-circular>
          <p class="mt-3">Loading news...</p>
        </v-col>
      </v-row>

      <v-row v-else class="news-grid" justify="start">
        <v-col
          v-for="(item, index) in news"
          :key="index"
          cols="12" sm="6" md="4" lg="2.4"
          class="d-flex"
        >
          <v-card 
            class="news-card flex-grow-1" 
            elevation="3"
            hover
            @click="openNews(item, index)"
          >
            <v-img
              :src="item.imageUrl"
              height="140"
              cover
              class="news-image"
            >
              <template v-slot:placeholder>
                <v-row
                  class="fill-height ma-0"
                  align="center"
                  justify="center"
                >
                  <v-icon size="48" color="grey lighten-3">mdi-image</v-icon>
                </v-row>
              </template>
            </v-img>
            
            <v-card-text class="pa-2">
              <h4 class="news-title text-body-2 font-weight-bold">
                {{ item.title }}
              </h4>
              <p class="news-excerpt text-caption text-grey mt-1 mb-0">
                {{ item.excerpt }}
              </p>
            </v-card-text>
            
            <v-card-actions class="pa-2 pt-0">
              <div class="d-flex flex-wrap">
                <v-chip
                  x-small
                  :color="getSentimentColor(item.hmm)"
                  dark
                  v-if="item.hmm"
                  class="mr-1 mb-1"
                >
                  H: {{ item.hmm }}
                </v-chip>
                <v-chip
                  x-small
                  :color="getSentimentColor(item.mlp)"
                  dark
                  v-if="item.mlp"
                  class="mr-1 mb-1"
                >
                  M: {{ item.mlp }}
                </v-chip>
              </div>
            </v-card-actions>
          </v-card>
        </v-col>

        <v-col v-if="!loading && news.length === 0" cols="12" class="text-center">
          <v-icon size="64" color="grey">mdi-newspaper-variant-outline</v-icon>
          <p class="text-h6 text-grey mt-3">No news found</p>
        </v-col>
      </v-row>

      <v-row class="mt-6" justify="center">
        <v-col cols="auto">
          <div class="pagination-controls d-flex align-center">
            <v-btn
              icon
              large
              :disabled="currentPage <= 1 || loading"
              @click="previousPage"
              class="mx-2"
            >
              <v-icon size="32">mdi-chevron-left</v-icon>
            </v-btn>

            <div class="page-info mx-4">
              <span class="text-h6 font-weight-bold">{{ currentPage }}</span>
              <span class="text-body-2 text-grey mx-2">of</span>
              <span class="text-h6 font-weight-bold">{{ totalPages || '?' }}</span>
            </div>

       
            <v-btn
              icon
              large
              :disabled="!hasNextPage || loading"
              @click="nextPage"
              class="mx-2"
            >
              <v-icon size="32">mdi-chevron-right</v-icon>
            </v-btn>
          </div>
        </v-col>
      </v-row>

      <v-row class="mt-4" justify="center" v-if="totalPages > 5">
        <v-col cols="auto">
          <div class="d-flex align-center">
            <span class="text-caption mr-3">Jump to page:</span>
            <v-text-field
              v-model="jumpToPage"
              type="number"
              :min="1"
              :max="totalPages"
              dense
              outlined
              hide-details
              style="width: 80px"
              @keyup.enter="goToPage"
            ></v-text-field>
            <v-btn
              small
              color="primary"
              class="ml-2"
              @click="goToPage"
              :disabled="!isValidJumpPage"
            >
              Go
            </v-btn>
          </div>
        </v-col>
      </v-row>

      <v-row class="mt-4" justify="center" v-if="$vuetify.breakpoint.mdAndUp">
        <v-col cols="auto">
          <v-chip small outlined color="info">
            API: {{ baseURL }}/news?page={{ currentPage }}&limit=15
          </v-chip>
        </v-col>
      </v-row>
    </v-container>
  </section>
</template>

<script>
export default {
  data() {
    return {
      loading: true,
      currentPage: 1,
      totalPages: null,
      totalArticles: null,
      hasNextPage: false,
      jumpToPage: '',
      news: [],
      baseURL: 'http://127.0.0.1:8000/api/v1' 
    };
  },
  
  computed: {
    isValidJumpPage() {
      const page = parseInt(this.jumpToPage);
      return page >= 1 && page <= this.totalPages;
    }
  },
  
  methods: {
    async loadNews(page = 1) {
      this.loading = true;
      
      try {
        const response = await fetch(`${this.baseURL}/news?page=${page}&limit=15`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        this.news = data.news.map(item => ({
          title: item.title || 'No Title',
          imageUrl: item.img || 'https://via.placeholder.com/300x140?text=No+Image',
          hmm: item.hmm,
          mlp: item.mlp,
          excerpt: this.getSentimentText(item.hmm, item.mlp)
        }));
        
        this.currentPage = data.page;
        this.hasNextPage = data.has_more;
        this.totalArticles = data.total;
        
        // Calculate total pages
        if (data.total) {
          this.totalPages = Math.ceil(data.total / 15);
        }
        
        // Scroll to top after loading
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
      } catch (error) {
        console.error('Error loading news:', error);
        this.news = [];
        this.$toast?.error?.('Failed to load news. Please try again.') || 
        alert('Failed to load news. Please try again.');
      } finally {
        this.loading = false;
      }
    },
    
    async nextPage() {
      if (this.hasNextPage && !this.loading) {
        await this.loadNews(this.currentPage + 1);
      }
    },
    
    async previousPage() {
      if (this.currentPage > 1 && !this.loading) {
        await this.loadNews(this.currentPage - 1);
      }
    },
    
    async goToPage() {
      const page = parseInt(this.jumpToPage);
      if (this.isValidJumpPage && page !== this.currentPage && !this.loading) {
        await this.loadNews(page);
        this.jumpToPage = '';
      }
    },
    
    getSentimentText(hmm, mlp) {
      const sentiments = [];
      if (hmm) sentiments.push(`HMM: ${hmm}`);
      if (mlp) sentiments.push(`MLP: ${mlp}`);
      return sentiments.length > 0 ? sentiments.join(' | ') : 'No sentiment analysis';
    },
    
    getSentimentColor(sentiment) {
      if (!sentiment) return 'grey';
      
      switch(sentiment.toLowerCase()) {
        case 'positive': return 'green';
        case 'negative': return 'red';
        case 'neutral': return 'blue-grey';
        default: return 'grey';
      }
    },
    
    openNews(item, index) {
      console.log('Opening news:', item);
      // Handle news item click
      // this.$router.push(`/news/${item.id}`);
    }
  },
  
  async mounted() {
    await this.loadNews(1);
  }
};
</script>

<style scoped>
#news {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 40px 0;
  min-height: 100vh;
}

.news-grid {
  min-height: 400px;
}

.news-card {
  height: 280px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
}

.news-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.15) !important;
}

.news-image {
  flex-shrink: 0;
}

.news-title {
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #1a1a1a;
  height: 32px;
}

.news-excerpt {
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 32px;
}

.pagination-controls {
  background: white;
  padding: 16px 24px;
  border-radius: 50px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.page-info {
  min-width: 120px;
  text-align: center;
}

@media (min-width: 1264px) {
  .news-grid .v-col {
    flex: 0 0 20%;
    max-width: 20%;
  }
}

@media (max-width: 1263px) {
  .news-grid .v-col {
    flex: 0 0 33.333333%;
    max-width: 33.333333%;
  }
}

@media (max-width: 959px) {
  .news-grid .v-col {
    flex: 0 0 50%;
    max-width: 50%;
  }
  
  .news-card {
    height: 260px;
  }
}

@media (max-width: 599px) {
  .news-grid .v-col {
    flex: 0 0 100%;
    max-width: 100%;
  }
  
  .news-card {
    height: 300px;
  }
  
  .pagination-controls {
    padding: 12px 20px;
  }
}

/* Animation for smooth transitions */
.news-grid {
  transition: opacity 0.3s ease;
}

.loading .news-grid {
  opacity: 0.6;
}

/* Custom button styles */
.v-btn--icon.v-size--large {
  height: 56px !important;
  width: 56px !important;
}

.v-btn--icon.v-size--large .v-icon {
  font-size: 32px !important;
}

/* Hover effects for pagination */
.pagination-controls .v-btn:not(.v-btn--disabled):hover {
  background-color: #f5f5f5;
}
</style>