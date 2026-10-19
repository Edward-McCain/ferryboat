<script setup>
import { routeEnds } from "../copy";

defineProps({
  crossing: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  failed: {
    type: Boolean,
    default: false,
  },
});
</script>

<template>
  <aside class="plate">
    <template v-if="loading || failed">
      <p class="plate-meta">{{ failed ? "Лист не открылся." : "Открываю лист." }}</p>
    </template>
    <template v-else-if="crossing">
      <p class="plate-time">{{ crossing.departure }}</p>
      <p class="plate-state">
        {{ crossing.status === "boarding" ? "Сейчас на посадке" : "Следующий отход" }}
      </p>
      <p class="route">
        <span>{{ routeEnds(crossing.direction)[0] }}</span>
        <span class="route-line" aria-hidden="true"></span>
        <span>{{ routeEnds(crossing.direction)[1] }}</span>
      </p>
      <p class="plate-meta">Причал {{ crossing.berth }}, {{ crossing.capacity }} мест</p>
    </template>
    <template v-else>
      <p class="plate-state plate-state-lone">Открытых рейсов нет</p>
      <p class="plate-meta">Посадка начнётся, когда в листе появится рейс.</p>
    </template>
  </aside>
</template>
