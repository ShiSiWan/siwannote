<template>
  <nav class="mb-3 flex items-center justify-between py-2 md:mb-6">
    <!-- Brand Logo -->
    <RouterLink
      :to="{ name: 'home' }"
      v-if="!hideLogo"
      class="navbar-brand-logo flex items-center gap-2 transition-all hover:opacity-90"
    >
      <Logo responsive />
    </RouterLink>
    <div v-else></div>

    <!-- Right spacing placeholder for fixed top-right buttons -->
    <div class="hidden sm:block sm:w-20 md:w-24"></div>
  </nav>
</template>

<script setup>
import { RouterLink } from "vue-router";
import Logo from "../components/Logo.vue";

defineProps({
  hideLogo: Boolean,
});
</script>

<style scoped>
/* Desktop only: Offset logo when sidebar is closed to not overlap top-left action box */
@media (min-width: 768px) {
  :global(body:not(.fn-sidebar-open)) .navbar-brand-logo {
    padding-left: 11rem;
  }

  :global(body.fn-sidebar-open) .navbar-brand-logo {
    padding-left: 0.5rem;
  }
}

/* Mobile: Perfectly centered and natural alignment */
@media (max-width: 767px) {
  .navbar-brand-logo {
    padding-left: 0 !important;
  }
}
</style>
