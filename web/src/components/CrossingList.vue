<script setup>
import { routeEnds, statusLabel } from "../copy";

defineProps({
  crossings: {
    type: Array,
    required: true,
  },
  pending: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["edit", "status", "remove"]);

function actions(status) {
  // Кнопки повторяют переходы на сервере. Если разойдутся, ответ 409 всё равно остановит смену.
  if (status === "scheduled") {
    return [
      { status: "boarding", label: "Начать посадку" },
      { status: "cancelled", label: "Отменить рейс" },
    ];
  }
  if (status === "boarding") {
    return [
      { status: "departed", label: "Отметить отход" },
      { status: "cancelled", label: "Отменить рейс" },
    ];
  }
  return [];
}
</script>

<template>
  <p v-if="crossings.length === 0" class="empty">На эту ночь рейсов нет. Добавьте первый.</p>
  <ul v-else class="rows">
    <li v-for="item in crossings" :key="item.id" class="row" :class="`is-${item.status}`">
      <p class="row-time">{{ item.departure }}</p>
      <div class="row-body">
        <p class="route route-compact">
          <span>{{ routeEnds(item.direction)[0] }}</span>
          <span class="route-line" aria-hidden="true"></span>
          <span>{{ routeEnds(item.direction)[1] }}</span>
        </p>
        <p class="row-meta">Причал {{ item.berth }}, {{ item.capacity }} мест</p>
        <p v-if="item.note" class="row-note">{{ item.note }}</p>
      </div>
      <p class="row-status">{{ statusLabel[item.status] }}</p>
      <div class="row-actions">
        <button
          v-if="item.status === 'scheduled'"
          type="button"
          class="text-button"
          :disabled="pending"
          @click="emit('edit', item)"
        >
          Поправить
        </button>
        <button
          v-for="action in actions(item.status)"
          :key="action.status"
          type="button"
          class="text-button"
          :disabled="pending"
          @click="emit('status', { id: item.id, status: action.status })"
        >
          {{ action.label }}
        </button>
        <button
          v-if="item.status === 'scheduled' || item.status === 'cancelled'"
          type="button"
          class="text-button text-button-danger"
          :disabled="pending"
          @click="emit('remove', item.id)"
        >
          Убрать из листа
        </button>
      </div>
    </li>
  </ul>
</template>
