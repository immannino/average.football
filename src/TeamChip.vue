<script setup>
import { inject } from 'vue'
defineProps({ team: String, bold: Boolean })
const logos = inject('logos', {})
</script>

<template>
  <a :href="`#team=${team}`" class="chip"><img v-if="logos[team]" :src="logos[team]" alt="" width="16" height="16" loading="lazy" /><b v-if="bold">{{ team }}</b><template v-else>{{ team }}</template></a>
</template>
