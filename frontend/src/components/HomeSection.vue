  <template>
    <section id="hero">
      <v-parallax dark src="@/assets/img/bgHero.jpg" height="750">
        <v-row align="center" justify="center">
          <v-col cols="10">
            <v-row align="center" justify="center">
              <v-col cols="12" md="6" xl="8">
                <h1 class="display-2 font-weight-bold mb-4">News Track Sentiment</h1>
                <h1 class="font-weight-light">
                 Always Get Updated <br />
                </h1>
                <v-btn
                  rounded
                  outlined
                  large
                  dark
                  @click="$vuetify.goTo('#features')"
                  class="mt-5"
                >
                  News
                  <v-icon class="ml-2">mdi-arrow-down</v-icon>
                </v-btn>
              </v-col>
              <v-col cols="12" md="6" xl="4" class="hidden-sm-and-down"> </v-col>
            </v-row>
          </v-col>
        </v-row>
        <div class="svg-border-waves text-white">
          <v-img src="@/assets/img/borderWaves.svg" />
        </div>
      </v-parallax>
      <v-container fluid id="features" class="mt-2">
        <v-row align="center" justify="center">
          <v-col cols="10">
            <v-row align="center" justify="space-around">
              <!-- <v-col cols="12" class="text-center">
                <h1 class="font-weight-light display-2">Title</h1>
                <h1 class="font-weight-light">
                  Lorem ipsum dolor sit amet consectetur adipisicing elit.
                </h1>
              </v-col> -->
              <v-col
                cols="12"
                sm="4"
                class="text-center"
                v-for="(feature, i) in features"
                :key="i"
              >
                <v-hover v-slot:default="{ hover }">
                  <v-card
                    class="card"
                    shaped
                    :elevation="hover ? 10 : 4"
                    :class="{ up: hover }"
                  >
                    <v-img
                      :src="feature.img"
                      max-width="100px"
                      class="d-block ml-auto mr-auto"
                      :class="{ 'zoom-efect': hover }"
                    ></v-img>
                    <h1 class="font-weight-regular">{{ feature.title }}</h1>
                    <h4 class="font-weight-regular subtitle-1">
                      {{ feature.text }}
                    </h4>
                  </v-card>
                </v-hover>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </v-container>
      <v-dialog v-model="dialog" max-width="640px">
        <v-card>
          <youtube
            :video-id="videoId"
            @ready="ready"
            @playing="playing"
          ></youtube>
        </v-card>
      </v-dialog>
      <div class="svg-border-waves">
        <img src="~@/assets/img/wave2.svg" />
      </div>
    </section>
  </template>

<script>
export default {
  data() {
    return {
      dialog: false,
      videoId: "i8IvvHJssWE",
      features: [
        {
          img: require("@/assets/img/icon2.png"),
          title: "HMM",
          text: "",
        },
        {
          img: require("@/assets/img/icon1.png"),
          title: "MLP",
          text: "",
        },

      ],
    };
  },
  watch: {
    dialog(value) {
      if (!value) {
        this.pause();
      }
    },
  },
  methods: {
    ready(event) {
      this.player = event.target;
    },
    playing(event) {
    },
    change() {

      this.videoId = "another video id";
    },
    stop() {
      this.player.stopVideo();
    },
    pause() {
      this.player.pauseVideo();
    },
  },
};
</script>

<style lang="scss">
.circle {
  stroke: white;
  stroke-dasharray: 650;
  stroke-dashoffset: 650;
  -webkit-transition: all 0.5s ease-in-out;
  opacity: 0.3;
}

.playBut {
  display: inline-block;
  -webkit-transition: all 0.5s ease;

  .triangle {
    -webkit-transition: all 0.7s ease-in-out;
    stroke-dasharray: 240;
    stroke-dashoffset: 480;
    stroke: white;
    transform: translateY(0);
  }

  &:hover {
    .triangle {
      stroke-dashoffset: 0;
      opacity: 1;
      stroke: white;
      animation: nudge 0.7s ease-in-out;

      @keyframes nudge {
        0% {
          transform: translateX(0);
        }
        30% {
          transform: translateX(-5px);
        }
        50% {
          transform: translateX(5px);
        }
        70% {
          transform: translateX(-2px);
        }
        100% {
          transform: translateX(0);
        }
      }
    }

    .circle {
      stroke-dashoffset: 0;
      opacity: 1;
    }
  }
}
</style>

<style>
.btn-play {
  transition: 0.2s;
}

.svg-border-waves .v-image {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3rem;
  width: 100%;
  overflow: hidden;
}

#hero {
  z-index: 0;
}
.svg-border-waves img {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  margin-bottom: -2px;
  z-index: -1;
}

.card {
  min-height: 300px;
  padding: 10px;
  transition: 0.5s ease-out;
}

.card .v-image {
  margin-bottom: 15px;
  transition: 0.75s;
}

.card h1 {
  margin-bottom: 10px;
}

.zoom-efect {
  transform: scale(1.1);
}

.up {
  transform: translateY(-20px);
  transition: 0.5s ease-out;
}
</style>

<style>
section {
  position: relative;
}
</style>
