<template>
  <v-footer dark padless>
    <v-card flat tile class="secondary white--text text-center">


      <v-card-text class="white--text pt-2">
        Website ini dibuat untuk memenuhi tugas Ujian Akhir Semester.
      </v-card-text>

      <v-divider></v-divider>

      <v-card-text class="white--text">
        {{ new Date().getFullYear() }} — <strong>Pembelajaran Mesin Dasar</strong>
      </v-card-text>
    </v-card>
  </v-footer>
</template>

<style scoped>
.v-card {
  width: 100%;
}
</style>

<script>
export default {
  data: () => ({
    icons: [
      {
        text: "mdi-facebook",
        link: "",
      },
      {
        text: "mdi-twitter",
        link: "",
      },
      {
        text: "mdi-linkedin",
        link: "",
      },
      {
        text: "mdi-instagram",
        link: "https://instagram.com/joabson_arley/",
      },
    ],
  }),
};
</script>
